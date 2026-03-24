"""
Google & X (Twitter) OAuth 2.0 — code exchange, user upsert, JWT issuance.

Flow (both providers):
  1. Frontend redirects user to provider consent URL (built client-side).
  2. Provider redirects back to frontend callback route with ?code=...
  3. Frontend POSTs the code to /api/auth/google or /api/auth/x
  4. This module exchanges the code for tokens, fetches the user profile,
     upserts the user row, and returns a ChannelZero JWT.
"""

from __future__ import annotations

import base64
from uuid import UUID

import httpx
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from ..config import get_settings
from ..db import get_conn
from .service import create_access_token

router = APIRouter()


# ── Request / Response schemas ────────────────────────────────────────────────

class OAuthCallbackRequest(BaseModel):
    code: str
    code_verifier: str | None = None  # Required for X (PKCE)


class OAuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


# ── Shared helper: find-or-create user by provider ID ─────────────────────────

async def upsert_oauth_user(provider: str, profile: dict) -> dict:
    """
    Look up a user by their provider ID (google_id / x_id).
    If not found, create a new row. Returns a dict with id, email, display_name.
    """
    id_column = f"{provider}_id"
    provider_id = profile.get(id_column)

    async with get_conn() as conn:
        # Try to find existing user by provider ID
        row = await conn.fetchrow(
            f"SELECT id, email, display_name, avatar_url FROM users WHERE {id_column} = $1",
            provider_id,
        )

        if row:
            # Update display_name / avatar if changed
            await conn.execute(
                f"""
                UPDATE users
                SET display_name = COALESCE($2, display_name),
                    avatar_url   = COALESCE($3, avatar_url),
                    updated_at   = now()
                WHERE {id_column} = $1
                """,
                provider_id,
                profile.get("display_name"),
                profile.get("avatar_url"),
            )
            return dict(row)

        # If user has an email, check for existing email-based account to link
        email = profile.get("email")
        if email:
            existing = await conn.fetchrow(
                "SELECT id, email, display_name, avatar_url FROM users WHERE email = $1",
                email,
            )
            if existing:
                # Link the provider to the existing account
                await conn.execute(
                    f"UPDATE users SET {id_column} = $1, avatar_url = COALESCE($2, avatar_url), updated_at = now() WHERE email = $3",
                    provider_id,
                    profile.get("avatar_url"),
                    email,
                )
                return dict(existing)

        # Create new user (no password_hash — OAuth-only)
        new_row = await conn.fetchrow(
            f"""
            INSERT INTO users (email, display_name, avatar_url, {id_column})
            VALUES ($1, $2, $3, $4)
            RETURNING id, email, display_name, avatar_url
            """,
            email or f"{provider}_{provider_id}@oauth.local",
            profile.get("display_name"),
            profile.get("avatar_url"),
            provider_id,
        )
        return dict(new_row)


# ── Google OAuth ──────────────────────────────────────────────────────────────

@router.post("/google", response_model=OAuthTokenResponse)
async def google_oauth_callback(req: OAuthCallbackRequest):
    """Exchange a Google authorization code for tokens, fetch profile, issue JWT."""
    settings = get_settings()
    if not settings.google_client_id:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Google OAuth not configured")

    async with httpx.AsyncClient(timeout=20.0) as client:
        # 1. Exchange code for tokens
        token_res = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "code": req.code,
                "grant_type": "authorization_code",
                "redirect_uri": settings.google_redirect_uri,
            },
        )
        if token_res.status_code != 200:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google token exchange failed")

        access_token = token_res.json().get("access_token")

        # 2. Fetch user profile
        user_info_res = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if user_info_res.status_code != 200:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to fetch Google profile")
        user_info = user_info_res.json()

    # 3. Upsert user
    user = await upsert_oauth_user("google", {
        "google_id": user_info.get("id"),
        "email": user_info.get("email"),
        "display_name": user_info.get("name"),
        "avatar_url": user_info.get("picture"),
    })

    jwt_token = create_access_token(UUID(str(user["id"])))
    return OAuthTokenResponse(access_token=jwt_token, user=user)


# ── X (Twitter) OAuth 2.0 with PKCE ──────────────────────────────────────────

@router.post("/x", response_model=OAuthTokenResponse)
async def x_oauth_callback(req: OAuthCallbackRequest):
    """Exchange an X authorization code + PKCE verifier for tokens, fetch profile, issue JWT."""
    if not req.code_verifier:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="code_verifier is required for X OAuth")

    settings = get_settings()
    if not settings.x_client_id:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="X OAuth not configured")

    # X requires Basic Auth for the token endpoint
    auth_str = base64.b64encode(f"{settings.x_client_id}:{settings.x_client_secret}".encode()).decode()

    async with httpx.AsyncClient(timeout=20.0) as client:
        # 1. Exchange code for tokens
        token_res = await client.post(
            "https://api.twitter.com/2/oauth2/token",
            headers={
                "Authorization": f"Basic {auth_str}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "code": req.code,
                "grant_type": "authorization_code",
                "client_id": settings.x_client_id,
                "redirect_uri": settings.x_redirect_uri,
                "code_verifier": req.code_verifier,
            },
        )
        if token_res.status_code != 200:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="X token exchange failed")

        access_token = token_res.json().get("access_token")

        # 2. Fetch user profile
        user_info_res = await client.get(
            "https://api.twitter.com/2/users/me?user.fields=profile_image_url",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if user_info_res.status_code != 200:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to fetch X profile")
        x_data = user_info_res.json().get("data", {})

    # 3. Upsert user
    user = await upsert_oauth_user("x", {
        "x_id": x_data.get("id"),
        "display_name": x_data.get("name"),
        "avatar_url": x_data.get("profile_image_url"),
        "email": None,  # X doesn't provide email without elevated access
    })

    jwt_token = create_access_token(UUID(str(user["id"])))
    return OAuthTokenResponse(access_token=jwt_token, user=user)
