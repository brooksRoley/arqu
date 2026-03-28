"""
Steam OpenID 2.0 authentication + Web API data ingestion.

Steam uses OpenID 2.0 (not OAuth 2.0). After identity verification,
we fetch game library + recent playtime via the Steam Web API to build
the "Isolation Metric" for the Oracle.

Flow:
  1. GET /steam/connect?token=<JWT>   → return OpenID auth URL
  2. GET /steam/callback?<openid...>  → verify identity, fetch games, store

Requires: STEAM_API_KEY (free from https://steamcommunity.com/dev/apikey)
"""

from __future__ import annotations

import json
import time
from urllib.parse import urlencode, parse_qs, urlparse
from uuid import UUID

import secrets

import httpx
import jwt
from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse, RedirectResponse

from ..auth.service import decode_access_token
from ..config import get_settings
from ..db import get_conn

router = APIRouter()

_STEAM_OPENID_URL = "https://steamcommunity.com/openid/login"
_STEAM_API_BASE = "https://api.steampowered.com"


# ── State helpers ─────────────────────────────────────────────────────────────

def _make_state(user_id: str) -> str:
    nonce = secrets.token_urlsafe(16)
    payload = {"sub": user_id, "nonce": nonce, "exp": int(time.time()) + 600}
    return jwt.encode(payload, get_settings().jwt_secret, algorithm="HS256")


async def _verify_state(state: str) -> str:
    try:
        payload = jwt.decode(state, get_settings().jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state") from exc

    nonce = payload.get("nonce")
    if not nonce:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid state — missing nonce")

    async with get_conn() as conn:
        try:
            await conn.execute(
                "INSERT INTO _oauth_nonces (nonce, consumed_at) VALUES ($1, now())",
                nonce,
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="State already consumed — possible replay attack",
            )

    return payload["sub"]


# ── Routes ───────────────────────────────────────────────────────────────────

@router.get("/connect")
async def steam_connect(token: str = Query(..., description="Frontend JWT")):
    """Return the Steam OpenID login URL."""
    settings = get_settings()
    if not settings.steam_api_key:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Steam not configured")

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    state = _make_state(payload["sub"])
    return_to = f"{settings.steam_redirect_uri}?state={state}"

    params = {
        "openid.ns": "http://specs.openid.net/auth/2.0",
        "openid.mode": "checkid_setup",
        "openid.return_to": return_to,
        "openid.realm": settings.cors_origin_list[0] if settings.cors_origin_list else "http://localhost:5173",
        "openid.identity": "http://specs.openid.net/auth/2.0/identifier_select",
        "openid.claimed_id": "http://specs.openid.net/auth/2.0/identifier_select",
    }
    return {"auth_url": f"{_STEAM_OPENID_URL}?{urlencode(params)}"}


@router.get("/callback")
async def steam_callback(request: Request):
    """
    Steam redirects here with OpenID params.
    Verify the assertion, extract Steam ID, fetch game data.
    """
    params = dict(request.query_params)

    # Extract and verify state
    state = params.get("state", "")
    if not state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing state parameter")
    user_id = await _verify_state(state)

    # Verify the OpenID assertion with Steam
    verify_params = dict(params)
    verify_params["openid.mode"] = "check_authentication"

    async with httpx.AsyncClient(timeout=20.0) as client:
        verify_resp = await client.post(_STEAM_OPENID_URL, data=verify_params)
        if "is_valid:true" not in verify_resp.text:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Steam OpenID verification failed")

    # Extract Steam ID from claimed_id
    claimed_id = params.get("openid.claimed_id", "")
    steam_id = claimed_id.split("/")[-1] if claimed_id else ""
    if not steam_id or not steam_id.isdigit():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not extract Steam ID")

    settings = get_settings()

    # Fetch game data via Steam Web API
    async with httpx.AsyncClient(timeout=20.0) as client:
        # Recently played games (last 2 weeks)
        recent_resp = await client.get(
            f"{_STEAM_API_BASE}/IPlayerService/GetRecentlyPlayedGames/v1/",
            params={"key": settings.steam_api_key, "steamid": steam_id},
        )
        recent_games = []
        if recent_resp.status_code == 200:
            recent_games = recent_resp.json().get("response", {}).get("games", [])

        # Full owned games with playtime
        owned_resp = await client.get(
            f"{_STEAM_API_BASE}/IPlayerService/GetOwnedGames/v1/",
            params={
                "key": settings.steam_api_key,
                "steamid": steam_id,
                "include_appinfo": "true",
                "include_played_free_games": "true",
            },
        )
        owned_games = []
        game_count = 0
        if owned_resp.status_code == 200:
            data = owned_resp.json().get("response", {})
            owned_games = data.get("games", [])
            game_count = data.get("game_count", 0)

        # Player summary for display name
        summary_resp = await client.get(
            f"{_STEAM_API_BASE}/ISteamUser/GetPlayerSummaries/v2/",
            params={"key": settings.steam_api_key, "steamids": steam_id},
        )
        persona_name = ""
        if summary_resp.status_code == 200:
            players = summary_resp.json().get("response", {}).get("players", [])
            if players:
                persona_name = players[0].get("personaname", "")

    # Distill isolation profile
    steam_profile = _distill_profile(steam_id, persona_name, recent_games, owned_games, game_count)

    # Store
    async with get_conn() as conn:
        if steam_id:
            await conn.execute(
                "UPDATE users SET steam_id = $1, updated_at = now() WHERE id = $2",
                steam_id, UUID(user_id),
            )

        await conn.execute(
            """
            UPDATE vibe_vectors
            SET steam_data = $2, updated_at = now()
            WHERE user_id = $1
            """,
            UUID(user_id), json.dumps(steam_profile),
        )

    # Redirect back to frontend
    frontend = settings.cors_origin_list[0] if settings.cors_origin_list else "http://localhost:5173"
    return RedirectResponse(f"{frontend}/peripheral?steam=connected")


# ── Profile distillation ─────────────────────────────────────────────────────

def _distill_profile(
    steam_id: str,
    persona_name: str,
    recent_games: list[dict],
    owned_games: list[dict],
    game_count: int,
) -> dict:
    """Reduce raw Steam data to isolation/gaming patterns."""
    # Recent playtime (last 2 weeks)
    recent_hours = round(sum(g.get("playtime_2weeks", 0) for g in recent_games) / 60, 1)
    recent_titles = [g.get("name", "Unknown") for g in recent_games[:10]]

    # Total lifetime playtime
    total_hours = round(sum(g.get("playtime_forever", 0) for g in owned_games) / 60, 1)

    # Top 10 most-played games
    sorted_games = sorted(owned_games, key=lambda g: g.get("playtime_forever", 0), reverse=True)
    top_games = [
        {"name": g.get("name", "Unknown"), "hours": round(g.get("playtime_forever", 0) / 60, 1)}
        for g in sorted_games[:10]
    ]

    # Single-player vs multiplayer heuristic:
    # Games with very high individual playtime + recent solo sessions suggest isolation
    heavy_solo_hours = sum(
        g.get("playtime_forever", 0) for g in sorted_games[:5]
    ) / 60 if sorted_games else 0

    return {
        "steam_id": steam_id,
        "persona_name": persona_name,
        "game_count": game_count,
        "recent_2week_hours": recent_hours,
        "recent_titles": recent_titles,
        "total_lifetime_hours": total_hours,
        "top_games": top_games,
        "heavy_session_hours": round(heavy_solo_hours, 1),
    }
