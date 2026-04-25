"""
Reddit OAuth + psychographic data ingestion.

Flow:
  1. GET /reddit/connect  → return auth URL for frontend redirect
  2. GET /reddit/callback → Reddit redirects back with ?code=&state=
                          → exchange code for tokens (Basic Auth)
                          → fetch user profile + subreddits + comments + saved
                          → encrypt tokens, store in oauth_tokens
                          → store Reddit profile in vibe_vectors.reddit_data
                          → redirect to frontend
"""

from __future__ import annotations

import base64
import json
import time
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

_REDDIT_AUTH_URL = "https://www.reddit.com/api/v1/authorize"
_REDDIT_TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
_REDDIT_API_BASE = "https://oauth.reddit.com"
_SCOPES = "identity read history"
_USER_AGENT = "channelzero/1.0"


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
async def reddit_connect(token: str = Query(..., description="Frontend JWT")):
    """
    Return the Reddit authorization URL for the authenticated user.
    Accepts the JWT as a query param because browser redirects can't set headers.
    """
    settings = get_settings()
    if not settings.reddit_client_id:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Reddit not configured")

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    params = {
        "client_id": settings.reddit_client_id,
        "response_type": "code",
        "redirect_uri": settings.reddit_redirect_uri,
        "scope": _SCOPES,
        "state": _make_state(payload["sub"]),
        "duration": "permanent",
    }
    return {"auth_url": f"{_REDDIT_AUTH_URL}?{urlencode(params)}"}


@router.get("/callback")
async def reddit_callback(code: str, state: str):
    """
    Reddit redirects here (via frontend) after user authorizes.
    Exchanges code for tokens, fetches profile + subreddits + comments, stores everything.
    """
    user_id = await _verify_state(state)
    settings = get_settings()

    # Reddit requires Basic Auth for token exchange
    credentials = base64.b64encode(
        f"{settings.reddit_client_id}:{settings.reddit_client_secret}".encode()
    ).decode()

    async with httpx.AsyncClient(timeout=20.0) as client:
        # 1. Exchange authorization code for access + refresh tokens
        token_resp = await client.post(
            _REDDIT_TOKEN_URL,
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": _USER_AGENT,
            },
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.reddit_redirect_uri,
            },
        )
        if token_resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Reddit token exchange failed: {token_resp.text}",
            )
        tokens = token_resp.json()

        access_token = tokens["access_token"]
        refresh_token = tokens.get("refresh_token", "")
        expires_in = tokens.get("expires_in", 3600)
        expires_at = int(time.time()) + expires_in

        api_headers = {
            "Authorization": f"Bearer {access_token}",
            "User-Agent": _USER_AGENT,
        }

        # 2. Fetch user profile
        me_resp = await client.get(f"{_REDDIT_API_BASE}/api/v1/me", headers=api_headers)
        me_data = {}
        if me_resp.status_code == 200:
            me_data = me_resp.json()

        # 3. Fetch subscribed subreddits
        subs_resp = await client.get(
            f"{_REDDIT_API_BASE}/subreddits/mine/subscriber",
            headers=api_headers,
            params={"limit": 100},
        )
        subs_data = []
        if subs_resp.status_code == 200:
            subs_data = subs_resp.json().get("data", {}).get("children", [])

        # 4. Fetch recent comments
        username = me_data.get("name", "")
        comments_data = []
        if username:
            comments_resp = await client.get(
                f"{_REDDIT_API_BASE}/user/{username}/comments",
                headers=api_headers,
                params={"limit": 50, "sort": "new"},
            )
            if comments_resp.status_code == 200:
                comments_data = comments_resp.json().get("data", {}).get("children", [])

        # 5. Fetch saved posts
        saved_data = []
        if username:
            saved_resp = await client.get(
                f"{_REDDIT_API_BASE}/user/{username}/saved",
                headers=api_headers,
                params={"limit": 50},
            )
            if saved_resp.status_code == 200:
                saved_data = saved_resp.json().get("data", {}).get("children", [])

        # 6. Fetch trophies
        trophies_data = []
        if username:
            trophies_resp = await client.get(
                f"{_REDDIT_API_BASE}/api/v1/me/trophies",
                headers=api_headers,
            )
            if trophies_resp.status_code == 200:
                trophies_data = trophies_resp.json().get("data", {}).get("trophies", [])

    # 7. Distill the psychographic profile
    reddit_profile = _distill_profile(me_data, subs_data, comments_data, saved_data, trophies_data)

    # 8. Encrypt and store tokens
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
            VALUES ($1, 'reddit', $2, $3, $4, $5, $6, $7)
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

        # 9. Store Reddit profile on vibe_vectors row (if intake already done)
        await conn.execute(
            """
            UPDATE vibe_vectors
            SET reddit_data = $2, updated_at = now()
            WHERE user_id = $1
            """,
            UUID(user_id), json.dumps(reddit_profile),
        )

    # Auto-trigger Oracle synthesis if enough providers connected
    await maybe_trigger_synthesis(UUID(user_id))

    # 10. Return success — frontend handles navigation
    return JSONResponse({"status": "connected", "username": reddit_profile.get("username", "")})


# ── Profile distillation ─────────────────────────────────────────────────────

@router.get("/profile")
async def get_reddit_profile(user_id: UUID = Depends(get_current_user_id)):
    """Return the stored Reddit profile for the current user, or null."""
    async with get_conn() as conn:
        row = await conn.fetchrow(
            "SELECT reddit_data FROM vibe_vectors WHERE user_id = $1",
            user_id,
        )
    if not row or not row["reddit_data"]:
        return None
    data = row["reddit_data"]
    return json.loads(data) if isinstance(data, str) else data


# ── Profile distillation ─────────────────────────────────────────────────────

def _distill_profile(
    me: dict,
    subreddits: list[dict],
    comments: list[dict],
    saved: list[dict],
    trophies: list[dict],
) -> dict:
    """Reduce raw Reddit data to psychographic essentials."""
    # Identity basics
    username = me.get("name", "")
    link_karma = me.get("link_karma", 0)
    comment_karma = me.get("comment_karma", 0)
    total_karma = link_karma + comment_karma
    created_utc = me.get("created_utc", 0)
    account_age_days = int((time.time() - created_utc) / 86400) if created_utc else 0

    # Karma ratio — lurker vs contributor signal
    karma_ratio = None
    if total_karma > 0:
        karma_ratio = round(comment_karma / total_karma, 3)

    # Top subreddits
    top_subs = []
    for s in subreddits:
        sub = s.get("data", {})
        top_subs.append({
            "name": sub.get("display_name", ""),
            "subscribers": sub.get("subscribers", 0),
        })
    top_subs.sort(key=lambda x: x["subscribers"], reverse=True)
    top_subs = top_subs[:30]

    # Comment activity — subreddit distribution + active hours
    comment_subs: dict[str, int] = {}
    active_hours: dict[int, int] = {}
    for c in comments:
        cd = c.get("data", {})
        sub = cd.get("subreddit", "")
        if sub:
            comment_subs[sub] = comment_subs.get(sub, 0) + 1
        created = cd.get("created_utc", 0)
        if created:
            hour = int((created % 86400) / 3600)
            active_hours[hour] = active_hours.get(hour, 0) + 1

    # Sort comment subs by frequency
    top_comment_subs = sorted(comment_subs.items(), key=lambda x: x[1], reverse=True)[:20]

    # Subreddit category diversity (unique subreddits across all signals)
    all_sub_names = set()
    for s in subreddits:
        name = s.get("data", {}).get("display_name", "")
        if name:
            all_sub_names.add(name)
    for sub_name, _ in top_comment_subs:
        all_sub_names.add(sub_name)

    # Trophy count
    trophy_count = len(trophies)
    trophy_names = [t.get("data", {}).get("name", "") for t in trophies if t.get("data", {}).get("name")]

    return {
        "username": username,
        "total_karma": total_karma,
        "link_karma": link_karma,
        "comment_karma": comment_karma,
        "comment_karma_ratio": karma_ratio,
        "account_age_days": account_age_days,
        "top_subreddits": top_subs,
        "comment_subreddits": [{"name": n, "count": c} for n, c in top_comment_subs],
        "active_hours": active_hours,
        "subreddit_diversity": len(all_sub_names),
        "trophy_count": trophy_count,
        "trophies": trophy_names[:10],
        "recent_comments_analyzed": len(comments),
        "saved_posts_analyzed": len(saved),
    }
