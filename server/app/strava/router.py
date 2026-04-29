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
from uuid import UUID

from ..oracle.trigger import maybe_trigger_synthesis

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from ..auth.deps import get_current_user_id
from ..config import get_settings
from ..db import get_conn
from ..oauth_base import (
from ..llm.chat import chat_completion
    build_authorize_url,
    make_oauth_state,
    store_oauth_tokens,
    store_provider_data,
    validate_connect_token,
    verify_oauth_state,
)

router = APIRouter()

_STRAVA_AUTH_URL = "https://www.strava.com/oauth/authorize"
_STRAVA_TOKEN_URL = "https://www.strava.com/oauth/token"
_STRAVA_API_BASE = "https://www.strava.com/api/v3"
_SCOPES = "read,activity:read"


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

    payload = validate_connect_token(token)

    url = build_authorize_url(
        _STRAVA_AUTH_URL,
        client_id=settings.strava_client_id,
        redirect_uri=settings.strava_redirect_uri,
        scope=_SCOPES,
        state=make_oauth_state(payload["sub"]),
        extra_params={"approval_prompt": "auto"},
    )
    return {"auth_url": url}


@router.get("/callback")
async def strava_callback(code: str, state: str):
    """
    Strava redirects here (via frontend) after user authorizes.
    Exchanges code for tokens, fetches athlete profile + activities, stores everything.
    """
    user_id = await verify_oauth_state(state)
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

    # 5. Store tokens + strava_id via shared helpers
    async with get_conn() as conn:
        strava_id = str(athlete.get("id", ""))
        if strava_id:
            await conn.execute(
                "UPDATE users SET strava_id = $1, updated_at = now() WHERE id = $2",
                strava_id, UUID(user_id),
            )

    await store_oauth_tokens(
        user_id, "strava", access_token, refresh_token, expires_at, _SCOPES,
    )

    # 6. Store Strava profile on vibe_vectors row (if intake already done)
    await store_provider_data(user_id, "strava_data", strava_profile)

    # Auto-trigger Oracle synthesis if enough providers connected
    await maybe_trigger_synthesis(UUID(user_id))

    # 7. Return success — frontend handles navigation
    return JSONResponse({"status": "connected", "athlete": strava_profile.get("athlete_name", "")})


# ── Profile distillation ─────────────────────────────────────────────────────

@router.get("/profile")
async def get_strava_profile(user_id: UUID = Depends(get_current_user_id)):
    """Return the stored Strava profile for the current user, or null."""
    async with get_conn() as conn:
        row = await conn.fetchrow(
            "SELECT strava_data FROM vibe_vectors WHERE user_id = $1",
            user_id,
        )
    if not row or not row["strava_data"]:
        return None
    data = row["strava_data"]
    return json.loads(data) if isinstance(data, str) else data


# ── Psychoanalysis ────────────────────────────────────────────────────────────

@router.get("/analyze")
async def strava_analyze(user_id: UUID = Depends(get_current_user_id)):
    """Generate an LLM psychoanalysis of the user's Strava somatic profile."""
    settings = get_settings()

    async with get_conn() as conn:
        row = await conn.fetchrow(
            "SELECT strava_data FROM vibe_vectors WHERE user_id = $1",
            user_id,
        )

    if not row or not row["strava_data"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No Strava data found")

    data = row["strava_data"]
    profile = json.loads(data) if isinstance(data, str) else data

    narrative = await _analyze_strava_profile(profile)
    return {"narrative": narrative}


async def _analyze_strava_profile(profile: dict) -> str:
    activity_types = profile.get("activity_types", {})
    activities_str = ", ".join(f"{k}: {v}" for k, v in activity_types.items())
    recent_count = profile.get("recent_count", 0)
    total_elevation = profile.get("total_elevation_m", 0)
    total_distance = profile.get("total_distance_km", 0)
    total_hours = profile.get("total_moving_hours", 0)
    avg_hr = profile.get("avg_heartrate")
    max_hr = profile.get("max_heartrate")
    all_runs = profile.get("all_time_runs", 0)
    all_run_km = profile.get("all_time_run_distance_km", 0)
    all_rides = profile.get("all_time_rides", 0)
    all_ride_km = profile.get("all_time_ride_distance_km", 0)

    prompt = f"""You are a perceptive behavioral psychologist analyzing a person's Strava athletic data as a window into their relationship with their body and discipline.
Your task: write a sharp, warm, 2-3 paragraph psychoanalysis of this user's somatic patterns and what they reveal about their inner life.
Do not be clinical. Be insightful, specific, and draw connections between data points.

SIGNAL DATA:
- Activity types (recent 30): {activities_str}
- Recent activities: {recent_count}
- Total elevation gain: {total_elevation}m
- Total distance: {total_distance}km
- Total moving time: {total_hours} hours
- Avg heart rate: {avg_hr or 'N/A'} bpm | Max heart rate: {max_hr or 'N/A'} bpm
- All-time runs: {all_runs} ({all_run_km}km)
- All-time rides: {all_rides} ({all_ride_km}km)

Write 2-3 paragraphs analyzing:
1. Relationship with the body — what activity choices and volume reveal about how they inhabit their physical form, whether movement is escape or communion
2. Discipline patterns — consistency, intensity preferences, competitive vs meditative tendencies
3. What elevation, distance, and heart rate patterns reveal about their relationship with suffering, endurance, and self-imposed limits

Be direct, specific, a little poetic. Avoid generic statements. Return only the narrative."""

    return await chat_completion(prompt)


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
