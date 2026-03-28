"""
ChannelZero API — FastAPI application entry point.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .db import init_pool, close_pool
from .auth.router import router as auth_router
from .auth.oauth import router as oauth_router
from .journal.router import router as journal_router
from .poll.router import router as poll_router
from .llm.router import router as llm_router
from .intake.router import router as intake_router
from .spotify.router import router as spotify_router
from .oracle.router import router as oracle_router
from .strava.router import router as strava_router
from .psychometrics.router import router as psychometrics_router
from .gcal.router import router as gcal_router
from .steam.router import router as steam_router
from .twitter.router import router as twitter_router
from .letterboxd.router import router as letterboxd_router
from .costar.router import router as costar_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: connect to DB. Shutdown: drain pool."""
    settings = get_settings()
    pool = await init_pool()

    # Run migrations check / stamp (lightweight — just verifies tables exist)
    async with pool.acquire() as conn:
        exists = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'users')"
        )
        if not exists and settings.debug:
            print("⚠  Tables not found. Run: python -m server.migrate")

    yield

    await close_pool()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="ChannelZero API",
        version="0.1.0",
        docs_url="/api/docs" if settings.debug else None,
        redoc_url=None,
        lifespan=lifespan,
    )

    # ── CORS ────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ─────────────────────────────────────────────────
    prefix = settings.api_prefix
    app.include_router(auth_router, prefix=f"{prefix}/auth", tags=["auth"])
    app.include_router(oauth_router, prefix=f"{prefix}/auth", tags=["oauth"])
    app.include_router(journal_router, prefix=f"{prefix}/journal", tags=["journal"])
    app.include_router(poll_router, prefix=f"{prefix}/poll", tags=["poll"])
    app.include_router(llm_router, prefix=f"{prefix}/llm", tags=["llm"])
    app.include_router(intake_router, prefix=f"{prefix}/intake", tags=["intake"])
    app.include_router(spotify_router, prefix=f"{prefix}/spotify", tags=["spotify"])
    app.include_router(oracle_router, prefix=f"{prefix}/oracle", tags=["oracle"])
    app.include_router(strava_router, prefix=f"{prefix}/strava", tags=["strava"])
    app.include_router(psychometrics_router, prefix=f"{prefix}/psychometrics", tags=["psychometrics"])
    app.include_router(gcal_router, prefix=f"{prefix}/gcal", tags=["gcal"])
    app.include_router(steam_router, prefix=f"{prefix}/steam", tags=["steam"])
    app.include_router(twitter_router, prefix=f"{prefix}/twitter", tags=["twitter"])
    app.include_router(letterboxd_router, prefix=f"{prefix}/letterboxd", tags=["letterboxd"])
    app.include_router(costar_router, prefix=f"{prefix}/costar", tags=["costar"])

    # ── Health ──────────────────────────────────────────────────
    @app.get("/health")
    async def health():
        return {"status": "ok", "service": "channelzero-api"}

    return app


app = create_app()
