"""
Lightweight migration runner — applies SQL files from server/migrations/ in order.
Tracks applied migrations in the _migrations table.

Usage:
    python -m server.app.migrate
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import asyncpg

from .config import get_settings


MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


async def run_migrations():
    settings = get_settings()
    conn = await asyncpg.connect(dsn=settings.database_url)

    try:
        # Ensure _migrations table exists
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS _migrations (
                id         SERIAL PRIMARY KEY,
                filename   TEXT UNIQUE NOT NULL,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
        """)

        # Get already applied
        applied = set()
        rows = await conn.fetch("SELECT filename FROM _migrations")
        for r in rows:
            applied.add(r["filename"])

        # Find and sort migration files
        sql_files = sorted(MIGRATIONS_DIR.glob("*.sql"))

        for f in sql_files:
            if f.name in applied:
                print(f"  ✓ {f.name} (already applied)")
                continue

            print(f"  → Applying {f.name}...")
            sql = f.read_text()
            await conn.execute(sql)
            print(f"  ✓ {f.name} applied")

        print("\nAll migrations up to date.")

    finally:
        await conn.close()


def main():
    print("ChannelZero — Running migrations\n")
    asyncio.run(run_migrations())


if __name__ == "__main__":
    main()
