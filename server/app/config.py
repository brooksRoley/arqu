"""
ChannelZero API — Configuration
Reads from environment variables (loaded from .env in dev via python-dotenv).
"""

from __future__ import annotations

import os
from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings


# Walk up from server/app/config.py to repo root to find .env
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    # ── Database (Vercel Postgres / Neon) ───────────────────────
    database_url: str
    database_url_unpooled: str = ""

    # ── Auth ────────────────────────────────────────────────────
    # No defaults — app MUST crash on boot if these are not set.
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440  # 24 hours

    # ── Encryption (for user API keys) ──────────────────────────
    # No default — app MUST crash on boot if not set.
    server_encryption_key: str

    # ── Pinecone ────────────────────────────────────────────────
    pinecone_api_key: str = ""
    pinecone_index: str = "channelzero"

    # ── Spotify OAuth ────────────────────────────────────────────
    spotify_client_id: str = ""
    spotify_client_secret: str = ""
    spotify_redirect_uri: str = "http://localhost:8000/api/spotify/callback"

    # ── Google OAuth ──────────────────────────────────────────────
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:5173/auth/google/callback"

    # ── X (Twitter) OAuth 2.0 ─────────────────────────────────────
    x_client_id: str = ""
    x_client_secret: str = ""
    x_redirect_uri: str = "http://localhost:5173/auth/x/callback"

    # ── Strava OAuth ─────────────────────────────────────────────────
    strava_client_id: str = ""
    strava_client_secret: str = ""
    strava_redirect_uri: str = "http://localhost:5173/auth/strava/callback"

    # ── Embeddings (server-level OpenAI key — NOT stored per-user) ──
    # Used exclusively for generating vibe vectors and journal embeddings.
    # Required for user matching and karma mechanics to function.
    openai_embed_key: str = ""

    # ── CORS ────────────────────────────────────────────────────
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # ── Server ──────────────────────────────────────────────────
    debug: bool = False
    api_prefix: str = "/api"

    model_config = {
        "env_file": str(_REPO_ROOT / ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",  # ignore PG* vars and other extras in .env
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()
