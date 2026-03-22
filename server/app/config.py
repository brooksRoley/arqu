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
    jwt_secret: str = "changeme-generate-a-real-secret"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440  # 24 hours

    # ── Encryption (for user API keys) ──────────────────────────
    server_encryption_key: str = "changeme-generate-a-32-byte-key"

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
