"""
YouTube OAuth + attention data ingestion.

Flow:
  1. GET /youtube/connect  → return auth URL for frontend redirect
  2. GET /youtube/callback → Google redirects back with ?code=&state=
                           → exchange code for tokens
                           → fetch channel info + subscriptions + liked videos
                           → encrypt tokens, store in oauth_tokens
                           → store YouTube profile in vibe_vectors.youtube_data
                           → redirect to frontend
"""

from __future__ import annotations

import json
import time
from urllib.parse import urlencode
from uuid import UUID

import secrets

from ..oracle.trigger import maybe_trigger_synthesis

import httpx
import jwt
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse

from ..auth.deps import get_current_user_id
from ..auth.service import decode_access_token
from ..config import get_settings
from ..db import get_conn
from ..llm.encryption import encrypt_api_key

router = APIRouter()

_GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"
_SCOPES = "https://www.googleapis.com/auth/youtube.readonly"


# ── State helpers ─────────────────────────────────────────────────────────────

def _make_state(user_id: str) -> str:
    nonce = secrets.token_urlsafe(16)
    payload = {"sub": user_id, "nonce": nonce, "exp": int(time.time()) + 600}
    return jwt.encode(payload, get_settings().jwt_secret, algorithm="HS256")


async def _verify_state(state: str) -> str:
    """Decode, verify, and consume the state JWT (one-time use)."""
    try:
        payload = jwt.decode(state, get_settings().jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state") from exc

    nonce = payload.get("nonce")
    if not nonce:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state — missing nonce")

    # Consume the nonce — INSERT fails on replay due to UNIQUE constraint
    async with get_conn() as conn:
        try:
            await conn.execute(
                """
                INSERT INTO _oauth_nonces (nonce, consumed_at)
                VALUES ($1, now())
                """,
                nonce,
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OAuth state already consumed — possible replay attack",
            )

    return payload["sub"]


# ── Routes ───────────────────────────────────────────────────────────────────

@router.get("/connect")
async def youtube_connect(token: str = Query(..., description="Frontend JWT")):
    """
    Return the YouTube authorization URL for the authenticated user.
    Accepts the JWT as a query param because browser redirects can't set headers.
    """
    settings = get_settings()
    if not settings.google_client_id:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Google OAuth not configured")

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.youtube_redirect_uri,
        "response_type": "code",
        "scope": _SCOPES,
        "state": _make_state(payload["sub"]),
        "access_type": "offline",
        "prompt": "consent",
    }
    return {"auth_url": f"{_GOOGLE_AUTH_URL}?{urlencode(params)}"}


@router.get("/callback")
async def youtube_callback(code: str, state: str):
    """
    Google redirects here (via frontend) after user authorizes.
    Exchanges code for tokens, fetches channel + subscriptions + liked videos, stores everything.
    """
    user_id = await _verify_state(state)
    settings = get_settings()

    async with httpx.AsyncClient(timeout=20.0) as client:
        # 1. Exchange authorization code for access + refresh tokens
        token_resp = await client.post(
            _GOOGLE_TOKEN_URL,
            data={
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": settings.youtube_redirect_uri,
            },
        )
        if token_resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"YouTube token exchange failed: {token_resp.text}",
            )
        tokens = token_resp.json()

        access_token = tokens["access_token"]
        refresh_token = tokens.get("refresh_token", "")
        expires_in = tokens.get("expires_in", 3600)
        expires_at = int(time.time()) + expires_in

        headers = {"Authorization": f"Bearer {access_token}"}

        # 2. Fetch authenticated user's channel info
        channel_resp = await client.get(
            f"{_YOUTUBE_API_BASE}/channels",
            headers=headers,
            params={"part": "snippet,statistics", "mine": "true"},
        )
        channel_data = {}
        if channel_resp.status_code == 200:
            items = channel_resp.json().get("items", [])
            if items:
                channel_data = items[0]

        # 3. Fetch subscriptions (up to 50)
        subs_resp = await client.get(
            f"{_YOUTUBE_API_BASE}/subscriptions",
            headers=headers,
            params={"part": "snippet", "mine": "true", "maxResults": 50, "order": "relevance"},
        )
        subs_data = []
        if subs_resp.status_code == 200:
            subs_data = subs_resp.json().get("items", [])

        # 4. Fetch liked videos playlist (contentDetails has relatedPlaylists.likes)
        liked_count = 0
        if channel_data:
            # Channel statistics includes the likeCount indirectly;
            # fetch the "likes" playlist to get count
            content_resp = await client.get(
                f"{_YOUTUBE_API_BASE}/channels",
                headers=headers,
                params={"part": "contentDetails", "mine": "true"},
            )
            if content_resp.status_code == 200:
                content_items = content_resp.json().get("items", [])
                if content_items:
                    likes_playlist = (
                        content_items[0]
                        .get("contentDetails", {})
                        .get("relatedPlaylists", {})
                        .get("likes", "")
                    )
                    if likes_playlist:
                        likes_resp = await client.get(
                            f"{_YOUTUBE_API_BASE}/playlists",
                            headers=headers,
                            params={"part": "contentDetails", "id": likes_playlist},
                        )
                        if likes_resp.status_code == 200:
                            pl_items = likes_resp.json().get("items", [])
                            if pl_items:
                                liked_count = pl_items[0].get("contentDetails", {}).get("itemCount", 0)

    # 5. Distill the attention profile
    youtube_profile = _distill_profile(channel_data, subs_data, liked_count)

    # 6. Encrypt and store tokens
    enc_access, access_nonce = encrypt_api_key(access_token)
    enc_refresh, refresh_nonce = encrypt_api_key(refresh_token) if refresh_token else (None, None)

    from datetime import datetime, timezone
    expires_dt = datetime.fromtimestamp(expires_at, tz=timezone.utc)

    async with get_conn() as conn:
        await conn.execute(
            """
            INSERT INTO oauth_tokens
                (user_id, provider, encrypted_access_token, access_nonce,
                 encrypted_refresh_token, refresh_nonce, expires_at, scope)
            VALUES ($1, 'youtube', $2, $3, $4, $5, $6, $7)
            ON CONFLICT (user_id, provider) DO UPDATE SET
                encrypted_access_token  = EXCLUDED.encrypted_access_token,
                access_nonce            = EXCLUDED.access_nonce,
                encrypted_refresh_token = EXCLUDED.encrypted_refresh_token,
                refresh_nonce           = EXCLUDED.refresh_nonce,
                expires_at              = EXCLUDED.expires_at,
                scope                   = EXCLUDED.scope,
                updated_at              = now()
            """,
            UUID(user_id),
            enc_access, access_nonce,
            enc_refresh, refresh_nonce,
            expires_dt, _SCOPES,
        )

        # 7. Store YouTube profile on vibe_vectors row (if intake already done)
        await conn.execute(
            """
            UPDATE vibe_vectors
            SET youtube_data = $2, updated_at = now()
            WHERE user_id = $1
            """,
            UUID(user_id), json.dumps(youtube_profile),
        )

    # Auto-trigger Oracle synthesis if enough providers connected
    await maybe_trigger_synthesis(UUID(user_id))

    # 8. Redirect to frontend
    frontend = settings.cors_origin_list[0] if settings.cors_origin_list else "http://localhost:5173"
    return RedirectResponse(f"{frontend}/calibrate?youtube=connected")


# ── Profile distillation ─────────────────────────────────────────────────────

@router.get("/profile")
async def get_youtube_profile(user_id: UUID = Depends(get_current_user_id)):
    """Return the stored YouTube profile for the current user, or null."""
    async with get_conn() as conn:
        row = await conn.fetchrow(
            "SELECT youtube_data FROM vibe_vectors WHERE user_id = $1",
            user_id,
        )
    if not row or not row["youtube_data"]:
        return None
    data = row["youtube_data"]
    return json.loads(data) if isinstance(data, str) else data


# ── Profile distillation ─────────────────────────────────────────────────────

def _distill_profile(channel: dict, subscriptions: list[dict], liked_count: int) -> dict:
    """Reduce raw YouTube data to the attention essentials."""
    snippet = channel.get("snippet", {})
    statistics = channel.get("statistics", {})

    # Channel basics
    channel_name = snippet.get("title", "")
    channel_description = snippet.get("description", "")
    published_at = snippet.get("publishedAt", "")

    subscriber_count = int(statistics.get("subscriberCount", 0))
    video_count = int(statistics.get("videoCount", 0))
    view_count = int(statistics.get("viewCount", 0))

    # Top subscriptions (channel names, up to 20)
    top_subs = []
    sub_categories: dict[str, int] = {}
    for sub in subscriptions[:20]:
        sub_snippet = sub.get("snippet", {})
        title = sub_snippet.get("title", "")
        if title:
            top_subs.append(title)
        # Extract category from description if available
        description = sub_snippet.get("description", "")
        if description:
            # Simple keyword-based categorization
            desc_lower = description.lower()
            for category in ["music", "gaming", "education", "comedy", "news", "sports",
                             "science", "technology", "entertainment", "cooking", "fitness",
                             "art", "travel", "fashion", "film"]:
                if category in desc_lower:
                    sub_categories[category] = sub_categories.get(category, 0) + 1

    # Subscription diversity: unique channels / total
    total_subs = len(subscriptions)

    return {
        "channel_name": channel_name,
        "channel_description": channel_description[:500] if channel_description else "",
        "subscriber_count": subscriber_count,
        "video_count": video_count,
        "view_count": view_count,
        "top_subscriptions": top_subs,
        "subscription_categories": sub_categories,
        "total_subscriptions": total_subs,
        "liked_videos_count": liked_count,
        "account_created": published_at,
        "subscription_diversity": len(top_subs),
    }
