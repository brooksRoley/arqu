"""
Strava OAuth + somatic data ingestion.

Flow:
  1. GET /strava/connect  → return auth URL for frontend redirect
  2. GET /strava/callback → Strava redirects back with ?code=&state=
                           → exchange code for tokens
                           → fetch athlete profile + recent activities
                           → encrypt tokens, store in oauth_tokens
                           → store Strava profile in vibe_vectors.strava_data
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
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse

from ..auth.service import decode_access_token
from ..config import get_settings
from ..db import get_conn
from ..llm.encryption import encrypt_api_key

router = APIRouter()

_STRAVA_AUTH_URL = "https://www.strava.com/oauth/authorize"
_STRAVA_TOKEN_URL = "https://www.strava.com/oauth/token"
_STRAVA_API_BASE = "https://www.strava.com/api/v3"
_SCOPES = "read,activity:read"


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
async def strava_connect(token: str = Query(..., description="Frontend JWT")):
    """
    Return the Strava authorization URL for the authenticated user.
    Accepts the JWT as a query param because browser redirects can't set headers.
    """
    settings = get_settings()
    if not settings.strava_client_id:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Strava not configured")

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    params = {
        "client_id": settings.strava_client_id,
        "response_type": "code",
        "redirect_uri": settings.strava_redirect_uri,
        "scope": _SCOPES,
        "state": _make_state(payload["sub"]),
        "approval_prompt": "auto",
    }
    return {"auth_url": f"{_STRAVA_AUTH_URL}?{urlencode(params)}"}


@router.get("/callback")
async def strava_callback(code: str, state: str):
    """
    Strava redirects here (via frontend) after user authorizes.
    Exchanges code for tokens, fetches athlete profile + activities, stores everything.
    """
    user_id = await _verify_state(state)
    settings = get_settings()

    async with httpx.AsyncClient(timeout=20.0) as client:
        # 1. Exchange authorization code for access + refresh tokens
        token_resp = await client.post(
            _STRAVA_TOKEN_URL,
            data={
                "client_id": settings.strava_client_id,
                "client_secret": settings.strava_client_secret,
                "code": code,
                "grant_type": "authorization_code",
            },
        )
        if token_resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Strava token exchange failed: {token_resp.text}",
            )
        tokens = token_resp.json()

        access_token = tokens["access_token"]
        refresh_token = tokens.get("refresh_token", "")
        expires_at = tokens.get("expires_at", int(time.time()) + 21600)
        athlete = tokens.get("athlete", {})

        headers = {"Authorization": f"Bearer {access_token}"}

        # 2. Fetch recent activities (last 30)
        activities_resp = await client.get(
            f"{_STRAVA_API_BASE}/athlete/activities",
            headers=headers,
            params={"per_page": 30},
        )
        activities_data = []
        if activities_resp.status_code == 200:
            activities_data = activities_resp.json()

        # 3. Fetch athlete stats
        athlete_id = athlete.get("id")
        stats_data = {}
        if athlete_id:
            stats_resp = await client.get(
                f"{_STRAVA_API_BASE}/athletes/{athlete_id}/stats",
                headers=headers,
            )
            if stats_resp.status_code == 200:
                stats_data = stats_resp.json()

    # 4. Distill the somatic profile
    strava_profile = _distill_profile(athlete, activities_data, stats_data)

    # 5. Encrypt and store tokens
    enc_access, access_nonce = encrypt_api_key(access_token)
    enc_refresh, refresh_nonce = encrypt_api_key(refresh_token) if refresh_token else (None, None)

    from datetime import datetime, timezone
    expires_dt = datetime.fromtimestamp(expires_at, tz=timezone.utc)

    async with get_conn() as conn:
        # Store strava_id on user
        strava_id = str(athlete.get("id", ""))
        if strava_id:
            await conn.execute(
                "UPDATE users SET strava_id = $1, updated_at = now() WHERE id = $2",
                strava_id, UUID(user_id),
            )

        await conn.execute(
            """
            INSERT INTO oauth_tokens
                (user_id, provider, encrypted_access_token, access_nonce,
                 encrypted_refresh_token, refresh_nonce, expires_at, scope)
            VALUES ($1, 'strava', $2, $3, $4, $5, $6, $7)
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

        # 6. Store Strava profile on vibe_vectors row (if intake already done)
        await conn.execute(
            """
            UPDATE vibe_vectors
            SET strava_data = $2, updated_at = now()
            WHERE user_id = $1
            """,
            UUID(user_id), json.dumps(strava_profile),
        )

    # Auto-trigger Oracle synthesis if enough providers connected
    await maybe_trigger_synthesis(UUID(user_id))

    # 7. Return success — frontend handles navigation
    return JSONResponse({"status": "connected", "athlete": strava_profile.get("athlete_name", "")})


# ── Profile distillation ─────────────────────────────────────────────────────

def _distill_profile(athlete: dict, activities: list[dict], stats: dict) -> dict:
    """Reduce raw Strava data to the somatic essentials."""
    # Athlete basics
    name = f"{athlete.get('firstname', '')} {athlete.get('lastname', '')}".strip()

    # Activity type distribution
    type_counts: dict[str, int] = {}
    total_elevation = 0.0
    total_distance = 0.0
    total_moving_time = 0
    heartrates: list[float] = []

    for a in activities:
        sport = a.get("type", "Unknown")
        type_counts[sport] = type_counts.get(sport, 0) + 1
        total_elevation += a.get("total_elevation_gain", 0)
        total_distance += a.get("distance", 0)
        total_moving_time += a.get("moving_time", 0)
        if a.get("average_heartrate"):
            heartrates.append(a["average_heartrate"])

    # Stats summary
    all_run_totals = stats.get("all_run_totals", {})
    all_ride_totals = stats.get("all_ride_totals", {})

    return {
        "athlete_name": name,
        "activity_types": type_counts,
        "recent_count": len(activities),
        "total_elevation_m": round(total_elevation, 1),
        "total_distance_km": round(total_distance / 1000, 1),
        "total_moving_hours": round(total_moving_time / 3600, 1),
        "avg_heartrate": round(sum(heartrates) / len(heartrates), 1) if heartrates else None,
        "max_heartrate": round(max(heartrates), 1) if heartrates else None,
        "all_time_runs": all_run_totals.get("count", 0),
        "all_time_run_distance_km": round(all_run_totals.get("distance", 0) / 1000, 1),
        "all_time_rides": all_ride_totals.get("count", 0),
        "all_time_ride_distance_km": round(all_ride_totals.get("distance", 0) / 1000, 1),
    }
