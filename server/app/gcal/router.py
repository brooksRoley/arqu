"""
Google Calendar OAuth + data ingestion.

Separate from the Google *auth* login flow — this requests calendar.readonly
scope to fetch event patterns and free/busy windows for the Oracle's
"Temporal Anxiety" dimension.

Flow:
  1. GET /gcal/connect?token=<JWT>  → redirect to Google with calendar scope
  2. GET /gcal/callback?code=&state= → exchange code, fetch events, store
"""

from __future__ import annotations

import json
import time
from urllib.parse import urlencode
from uuid import UUID

import secrets

import httpx
import jwt
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import RedirectResponse

from ..auth.service import decode_access_token
from ..config import get_settings
from ..db import get_conn
from ..llm.encryption import encrypt_api_key

router = APIRouter()

_GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GCAL_API_BASE = "https://www.googleapis.com/calendar/v3"
_SCOPES = "https://www.googleapis.com/auth/calendar.readonly"


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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state — missing nonce")

    async with get_conn() as conn:
        try:
            await conn.execute(
                "INSERT INTO _oauth_nonces (nonce, consumed_at) VALUES ($1, now())",
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
async def gcal_connect(token: str = Query(..., description="Frontend JWT")):
    """Redirect user to Google OAuth with calendar.readonly scope."""
    settings = get_settings()
    if not settings.google_client_id:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Google OAuth not configured")

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.gcal_redirect_uri,
        "response_type": "code",
        "scope": _SCOPES,
        "state": _make_state(payload["sub"]),
        "access_type": "offline",
        "prompt": "consent",
    }
    return RedirectResponse(f"{_GOOGLE_AUTH_URL}?{urlencode(params)}")


@router.get("/callback")
async def gcal_callback(code: str, state: str):
    """Google redirects here. Exchange code, fetch calendar data, store."""
    user_id = await _verify_state(state)
    settings = get_settings()

    async with httpx.AsyncClient(timeout=20.0) as client:
        # 1. Exchange code for tokens
        token_resp = await client.post(
            _GOOGLE_TOKEN_URL,
            data={
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": settings.gcal_redirect_uri,
            },
        )
        if token_resp.status_code != 200:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google token exchange failed")

        tokens = token_resp.json()
        access_token = tokens["access_token"]
        refresh_token = tokens.get("refresh_token", "")
        expires_in = tokens.get("expires_in", 3600)
        expires_at = int(time.time()) + expires_in

        headers = {"Authorization": f"Bearer {access_token}"}

        # 2. Fetch primary calendar event list (next 60 days)
        from datetime import datetime, timezone, timedelta
        now = datetime.now(tz=timezone.utc)
        time_min = now.isoformat()
        time_max = (now + timedelta(days=60)).isoformat()

        events_data = []
        events_resp = await client.get(
            f"{_GCAL_API_BASE}/calendars/primary/events",
            headers=headers,
            params={
                "timeMin": time_min,
                "timeMax": time_max,
                "maxResults": 100,
                "singleEvents": "true",
                "orderBy": "startTime",
            },
        )
        if events_resp.status_code == 200:
            events_data = events_resp.json().get("items", [])

        # 3. Fetch calendar list for context
        calendars = []
        cal_resp = await client.get(
            f"{_GCAL_API_BASE}/users/me/calendarList",
            headers=headers,
            params={"maxResults": 20},
        )
        if cal_resp.status_code == 200:
            calendars = cal_resp.json().get("items", [])

    # 4. Distill temporal profile
    gcal_profile = _distill_profile(events_data, calendars)

    # 5. Encrypt and store tokens
    enc_access, access_nonce = encrypt_api_key(access_token)
    enc_refresh, refresh_nonce = encrypt_api_key(refresh_token) if refresh_token else (None, None)

    from datetime import datetime as dt
    expires_dt = dt.fromtimestamp(expires_at, tz=timezone.utc)

    async with get_conn() as conn:
        await conn.execute(
            """
            INSERT INTO oauth_tokens
                (user_id, provider, encrypted_access_token, access_nonce,
                 encrypted_refresh_token, refresh_nonce, expires_at, scope)
            VALUES ($1, 'gcal', $2, $3, $4, $5, $6, $7)
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

        await conn.execute(
            """
            UPDATE vibe_vectors
            SET gcal_data = $2, updated_at = now()
            WHERE user_id = $1
            """,
            UUID(user_id), json.dumps(gcal_profile),
        )

    frontend = settings.cors_origin_list[0] if settings.cors_origin_list else "http://localhost:5173"
    return RedirectResponse(f"{frontend}/calibrate?gcal=connected")


# ── Profile distillation ─────────────────────────────────────────────────────

def _distill_profile(events: list[dict], calendars: list[dict]) -> dict:
    """Reduce raw Google Calendar data to temporal patterns."""
    total_events = len(events)
    calendar_count = len(calendars)

    # Bucket events by day-of-week and hour
    day_dist: dict[str, int] = {}
    hour_dist: dict[int, int] = {}
    recurring_count = 0
    all_day_count = 0

    for ev in events:
        start = ev.get("start", {})
        if "date" in start:
            all_day_count += 1
            continue

        dt_str = start.get("dateTime", "")
        if not dt_str:
            continue

        try:
            from datetime import datetime as dt
            parsed = dt.fromisoformat(dt_str.replace("Z", "+00:00"))
            day_name = parsed.strftime("%A")
            day_dist[day_name] = day_dist.get(day_name, 0) + 1
            hour_dist[parsed.hour] = hour_dist.get(parsed.hour, 0) + 1
        except (ValueError, TypeError):
            continue

        if ev.get("recurringEventId"):
            recurring_count += 1

    # Peak day and peak hour
    peak_day = max(day_dist, key=day_dist.get) if day_dist else None
    peak_hour = max(hour_dist, key=hour_dist.get) if hour_dist else None

    # Busyness: events per week (next 60 days ~ 8.5 weeks)
    events_per_week = round(total_events / 8.5, 1) if total_events else 0

    # Evening ratio (events after 6pm)
    evening_events = sum(v for k, v in hour_dist.items() if k >= 18)
    timed_events = sum(hour_dist.values())
    evening_ratio = round(evening_events / timed_events, 2) if timed_events else 0

    return {
        "total_events_60d": total_events,
        "events_per_week": events_per_week,
        "calendar_count": calendar_count,
        "recurring_ratio": round(recurring_count / total_events, 2) if total_events else 0,
        "all_day_count": all_day_count,
        "peak_day": peak_day,
        "peak_hour": peak_hour,
        "evening_ratio": evening_ratio,
        "day_distribution": day_dist,
    }
