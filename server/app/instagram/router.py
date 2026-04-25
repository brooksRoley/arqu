"""
Instagram OAuth + aesthetic data ingestion.

Flow:
  1. GET /instagram/connect  → return auth URL for frontend redirect
  2. GET /instagram/callback → Facebook redirects back with ?code=&state=
                              → exchange code for short-lived token
                              → exchange for long-lived Instagram token
                              → fetch user profile + recent media
                              → encrypt tokens, store in oauth_tokens
                              → store Instagram profile in vibe_vectors.instagram_data
                              → redirect to frontend
"""

from __future__ import annotations

import json
import time
from collections import Counter
from urllib.parse import urlencode
from uuid import UUID

import secrets

from ..oracle.trigger import maybe_trigger_synthesis

import httpx
import jwt
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from ..auth.deps import get_current_user_id
from ..auth.service import decode_access_token
from ..config import get_settings
from ..db import get_conn
from ..llm.encryption import encrypt_api_key

router = APIRouter()

_FB_AUTH_URL = "https://www.facebook.com/v21.0/dialog/oauth"
_FB_TOKEN_URL = "https://graph.facebook.com/v21.0/oauth/access_token"
_IG_API_BASE = "https://graph.instagram.com/v21.0"
_SCOPES = "instagram_basic,instagram_manage_insights"


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
async def instagram_connect(token: str = Query(..., description="Frontend JWT")):
    """
    Return the Instagram authorization URL for the authenticated user.
    Accepts the JWT as a query param because browser redirects can't set headers.
    """
    settings = get_settings()
    if not settings.instagram_client_id:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Instagram not configured")

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    params = {
        "client_id": settings.instagram_client_id,
        "response_type": "code",
        "redirect_uri": settings.instagram_redirect_uri,
        "scope": _SCOPES,
        "state": _make_state(payload["sub"]),
    }
    return {"auth_url": f"{_FB_AUTH_URL}?{urlencode(params)}"}


@router.get("/callback")
async def instagram_callback(code: str, state: str):
    """
    Facebook redirects here (via frontend) after user authorizes.
    Exchanges code for tokens, fetches profile + media, stores everything.
    """
    user_id = await _verify_state(state)
    settings = get_settings()

    async with httpx.AsyncClient(timeout=20.0) as client:
        # 1. Exchange authorization code for short-lived token
        token_resp = await client.get(
            _FB_TOKEN_URL,
            params={
                "client_id": settings.instagram_client_id,
                "client_secret": settings.instagram_client_secret,
                "redirect_uri": settings.instagram_redirect_uri,
                "code": code,
            },
        )
        if token_resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Instagram token exchange failed: {token_resp.text}",
            )
        short_lived_token = token_resp.json().get("access_token", "")

        # 2. Exchange short-lived token for long-lived Instagram token
        long_resp = await client.get(
            f"{_IG_API_BASE}/access_token",
            params={
                "grant_type": "ig_exchange_token",
                "client_secret": settings.instagram_client_secret,
                "access_token": short_lived_token,
            },
        )
        if long_resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Instagram long-lived token exchange failed: {long_resp.text}",
            )
        long_data = long_resp.json()
        access_token = long_data.get("access_token", short_lived_token)
        expires_in = long_data.get("expires_in", 5184000)  # default 60 days

        # 3. Fetch user profile
        profile_resp = await client.get(
            f"{_IG_API_BASE}/me",
            params={
                "fields": "id,username,account_type,media_count",
                "access_token": access_token,
            },
        )
        profile_data = {}
        if profile_resp.status_code == 200:
            profile_data = profile_resp.json()

        # 4. Fetch recent media
        media_resp = await client.get(
            f"{_IG_API_BASE}/me/media",
            params={
                "fields": "id,caption,media_type,timestamp,like_count,comments_count",
                "limit": 25,
                "access_token": access_token,
            },
        )
        media_data = []
        if media_resp.status_code == 200:
            media_data = media_resp.json().get("data", [])

    # 5. Distill the aesthetic profile
    instagram_profile = _distill_profile(profile_data, media_data)

    # 6. Encrypt and store tokens
    enc_access, access_nonce = encrypt_api_key(access_token)

    from datetime import datetime, timezone
    expires_at = int(time.time()) + expires_in
    expires_dt = datetime.fromtimestamp(expires_at, tz=timezone.utc)

    async with get_conn() as conn:
        await conn.execute(
            """
            INSERT INTO oauth_tokens
                (user_id, provider, encrypted_access_token, access_nonce,
                 encrypted_refresh_token, refresh_nonce, expires_at, scope)
            VALUES ($1, 'instagram', $2, $3, $4, $5, $6, $7)
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
            None, None,
            expires_dt, _SCOPES,
        )

        # 7. Store Instagram profile on vibe_vectors row (if intake already done)
        await conn.execute(
            """
            UPDATE vibe_vectors
            SET instagram_data = $2, updated_at = now()
            WHERE user_id = $1
            """,
            UUID(user_id), json.dumps(instagram_profile),
        )

    # Auto-trigger Oracle synthesis if enough providers connected
    await maybe_trigger_synthesis(UUID(user_id))

    # 8. Return success — frontend handles navigation
    return JSONResponse({"status": "connected", "username": instagram_profile.get("username", "")})


# ── Profile distillation ─────────────────────────────────────────────────────

@router.get("/profile")
async def get_instagram_profile(user_id: UUID = Depends(get_current_user_id)):
    """Return the stored Instagram profile for the current user, or null."""
    async with get_conn() as conn:
        row = await conn.fetchrow(
            "SELECT instagram_data FROM vibe_vectors WHERE user_id = $1",
            user_id,
        )
    if not row or not row["instagram_data"]:
        return None
    data = row["instagram_data"]
    return json.loads(data) if isinstance(data, str) else data


# ── Profile distillation ─────────────────────────────────────────────────────

def _distill_profile(profile: dict, media: list[dict]) -> dict:
    """Reduce raw Instagram data to the aesthetic essentials."""
    import re
    from datetime import datetime

    username = profile.get("username", "")
    account_type = profile.get("account_type", "personal")
    media_count = profile.get("media_count", 0)

    # Media type distribution
    type_counts: dict[str, int] = {}
    total_likes = 0
    total_comments = 0
    caption_lengths: list[int] = []
    all_hashtags: list[str] = []
    timestamps: list[datetime] = []

    for item in media:
        media_type = item.get("media_type", "UNKNOWN")
        type_counts[media_type] = type_counts.get(media_type, 0) + 1

        total_likes += item.get("like_count", 0)
        total_comments += item.get("comments_count", 0)

        caption = item.get("caption", "") or ""
        caption_lengths.append(len(caption))

        # Extract hashtags from captions
        hashtags = re.findall(r"#(\w+)", caption)
        all_hashtags.extend(hashtags)

        ts = item.get("timestamp")
        if ts:
            try:
                timestamps.append(datetime.fromisoformat(ts.replace("Z", "+00:00")))
            except (ValueError, AttributeError):
                pass

    n = len(media) or 1

    # Posting frequency (posts per week from recent media timestamps)
    posts_per_week = None
    if len(timestamps) >= 2:
        timestamps.sort()
        span_days = (timestamps[-1] - timestamps[0]).total_seconds() / 86400
        if span_days > 0:
            posts_per_week = round(len(timestamps) / (span_days / 7), 1)

    # Top hashtags
    hashtag_counts = Counter(all_hashtags)
    top_hashtags = [tag for tag, _ in hashtag_counts.most_common(15)]

    return {
        "username": username,
        "account_type": account_type,
        "media_count": media_count,
        "media_types": type_counts,
        "recent_count": len(media),
        "avg_caption_length": round(sum(caption_lengths) / n, 1),
        "posts_per_week": posts_per_week,
        "top_hashtags": top_hashtags,
        "avg_likes": round(total_likes / n, 1),
        "avg_comments": round(total_comments / n, 1),
        "total_likes": total_likes,
        "total_comments": total_comments,
    }
