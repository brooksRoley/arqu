"""
Spotify OAuth + data ingestion.

Flow:
  1. GET /spotify/connect  → redirect user to Spotify authorization page
  2. GET /spotify/callback → Spotify redirects back with ?code=&state=
                             → exchange code for tokens
                             → fetch top artists + audio features
                             → encrypt tokens, store in oauth_tokens
                             → store Spotify profile in vibe_vectors.spotify_data
                             → re-embed user's vibe vector with Spotify context blended in
                             → redirect to frontend
"""

from __future__ import annotations

import json
import time
from urllib.parse import urlencode
from uuid import UUID

import secrets

import httpx
import jwt
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse

from ..auth.deps import get_current_user_id
from ..auth.service import decode_access_token
from ..config import get_settings
from ..db import get_conn
from ..llm.encryption import encrypt_api_key, decrypt_api_key
from ..vector.service import upsert_user_vector

router = APIRouter()

_SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
_SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
_SPOTIFY_API_BASE = "https://api.spotify.com/v1"
_SCOPES = "user-top-read user-read-recently-played"


# ── State helpers ─────────────────────────────────────────────────────────────
# State is a JWT with a one-time nonce. After first use the nonce is consumed
# in the DB so the same state cannot be replayed within its TTL window.

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
async def spotify_connect(token: str = Query(..., description="Frontend JWT")):
    """
    Redirect the authenticated user to Spotify's authorization page.
    Accepts the JWT as a query param because browser redirects can't set headers.
    """
    settings = get_settings()
    if not settings.spotify_client_id:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Spotify not configured")

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    params = {
        "client_id": settings.spotify_client_id,
        "response_type": "code",
        "redirect_uri": settings.spotify_redirect_uri,
        "scope": _SCOPES,
        "state": _make_state(payload["sub"]),
        "show_dialog": "false",
    }
    return RedirectResponse(f"{_SPOTIFY_AUTH_URL}?{urlencode(params)}")


@router.get("/callback")
async def spotify_callback(code: str, state: str):
    """
    Spotify redirects here after user authorizes.
    Exchanges code for tokens, fetches audio profile, stores everything.
    """
    user_id = await _verify_state(state)
    settings = get_settings()

    async with httpx.AsyncClient(timeout=20.0) as client:
        # 1. Exchange authorization code for access + refresh tokens
        token_resp = await client.post(
            _SPOTIFY_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.spotify_redirect_uri,
            },
            auth=(settings.spotify_client_id, settings.spotify_client_secret),
        )
        token_resp.raise_for_status()
        tokens = token_resp.json()

        access_token = tokens["access_token"]
        refresh_token = tokens.get("refresh_token", "")
        expires_in = tokens.get("expires_in", 3600)
        scope = tokens.get("scope", "")
        expires_at = int(time.time()) + expires_in

        headers = {"Authorization": f"Bearer {access_token}"}

        # 2. Fetch top artists (medium-term ~6 months)
        artists_resp = await client.get(
            f"{_SPOTIFY_API_BASE}/me/top/artists",
            headers=headers,
            params={"limit": 10, "time_range": "medium_term"},
        )
        artists_resp.raise_for_status()
        artists_data = artists_resp.json().get("items", [])

        # 3. Fetch top tracks to get audio features
        tracks_resp = await client.get(
            f"{_SPOTIFY_API_BASE}/me/top/tracks",
            headers=headers,
            params={"limit": 20, "time_range": "medium_term"},
        )
        tracks_resp.raise_for_status()
        track_ids = [t["id"] for t in tracks_resp.json().get("items", [])]

        # 4. Fetch audio features for those tracks
        audio_features: list[dict] = []
        if track_ids:
            features_resp = await client.get(
                f"{_SPOTIFY_API_BASE}/audio-features",
                headers=headers,
                params={"ids": ",".join(track_ids)},
            )
            features_resp.raise_for_status()
            audio_features = [f for f in features_resp.json().get("audio_features", []) if f]

    # 5. Distill the audio profile
    spotify_profile = _distill_profile(artists_data, audio_features)

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
            VALUES ($1, 'spotify', $2, $3, $4, $5, $6, $7)
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
            expires_dt, scope,
        )

        # 7. Store Spotify profile on vibe_vectors row (if intake already done)
        await conn.execute(
            """
            UPDATE vibe_vectors
            SET spotify_data = $2, updated_at = now()
            WHERE user_id = $1
            """,
            UUID(user_id), json.dumps(spotify_profile),
        )

        # 8. Fetch full vibe vector to re-embed with Spotify context blended in
        row = await conn.fetchrow(
            "SELECT attachment_style, defense_mechanism, readiness_score FROM vibe_vectors WHERE user_id = $1",
            UUID(user_id),
        )

    # 9. Re-embed with Spotify data included — richer psychological coordinate
    if row:
        spotify_summary = _build_embedding_text(spotify_profile)
        confession_base = (
            f"Attachment: {row['attachment_style']}. "
            f"Defense: {row['defense_mechanism']}. "
            f"Readiness: {row['readiness_score']}."
        )
        await upsert_user_vector(
            user_id=user_id,
            confession_text=f"{confession_base} {spotify_summary}",
            attachment_style=row["attachment_style"],
            defense_mechanism=row["defense_mechanism"],
            readiness_score=row["readiness_score"],
        )

    # 10. Redirect back to frontend
    frontend = settings.cors_origin_list[0] if settings.cors_origin_list else "http://localhost:5173"
    return RedirectResponse(f"{frontend}/game?spotify=connected")


# ── Profile distillation ─────────────────────────────────────────────────────

def _distill_profile(artists: list[dict], features: list[dict]) -> dict:
    """Reduce raw Spotify data to the essentials we care about."""
    top_artist_names = [a["name"] for a in artists[:5]]
    genres: list[str] = []
    for a in artists[:5]:
        genres.extend(a.get("genres", []))
    # Deduplicate while preserving order
    seen: set = set()
    unique_genres = [g for g in genres if not (g in seen or seen.add(g))][:8]  # type: ignore[func-returns-value]

    avg: dict[str, float] = {}
    keys = ["valence", "danceability", "energy", "acousticness", "instrumentalness", "tempo"]
    if features:
        for k in keys:
            vals = [f[k] for f in features if k in f]
            avg[k] = round(sum(vals) / len(vals), 3) if vals else 0.0

    return {
        "top_artists": top_artist_names,
        "genres": unique_genres,
        "audio_avg": avg,
    }


def _build_embedding_text(profile: dict) -> str:
    """Convert Spotify profile to natural-language text for blending into embedding."""
    artists = ", ".join(profile.get("top_artists", []))
    genres = ", ".join(profile.get("genres", []))
    avg = profile.get("audio_avg", {})

    valence = avg.get("valence", 0)
    valence_label = "euphoric" if valence > 0.7 else ("melancholic" if valence < 0.35 else "ambivalent")
    energy = avg.get("energy", 0)
    energy_label = "high-intensity" if energy > 0.7 else ("introspective" if energy < 0.35 else "mid-energy")

    return (
        f"Top artists: {artists}. "
        f"Genres: {genres}. "
        f"Sonic valence: {valence:.2f} ({valence_label}), "
        f"danceability: {avg.get('danceability', 0):.2f}, "
        f"energy: {energy:.2f} ({energy_label})."
    )
