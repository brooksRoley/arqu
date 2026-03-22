"""
ChannelZero API — Database connection pool (asyncpg + Neon).
"""

from __future__ import annotations

import asyncpg
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from .config import get_settings

_pool: asyncpg.Pool | None = None


async def init_pool() -> asyncpg.Pool:
    """Create the connection pool. Called once during app lifespan startup."""
    global _pool
    settings = get_settings()

    # Neon with pgbouncer (pooled URL) — use statement-level prepared statements
    _pool = await asyncpg.create_pool(
        dsn=settings.database_url,
        min_size=1,
        max_size=5,
        statement_cache_size=0,  # required for pgbouncer compatibility
        command_timeout=30,
    )
    return _pool


async def close_pool() -> None:
    """Drain and close the pool. Called during app lifespan shutdown."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool:
    """Get the current pool. Raises if not initialized."""
    if _pool is None:
        raise RuntimeError("Database pool not initialized — call init_pool() first")
    return _pool


@asynccontextmanager
async def get_conn() -> AsyncGenerator[asyncpg.Connection, None]:
    """Acquire a connection from the pool as an async context manager."""
    pool = get_pool()
    async with pool.acquire() as conn:
        yield conn


@asynccontextmanager
async def get_tx() -> AsyncGenerator[asyncpg.Connection, None]:
    """Acquire a connection with a transaction."""
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            yield conn
