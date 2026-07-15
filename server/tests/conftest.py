"""
Shared test fixtures — a fake asyncpg connection and a get_conn patcher.

The fake conn is a recorder: queue fetchrow/fetchval results in order, and
every execute/fetchrow call is captured for assertion. Designed so future
connector-router tests can reuse it.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

import pytest


class FakeConn:
    """Minimal asyncpg.Connection stand-in.

    fetchrow_results are consumed FIFO; executes are recorded as
    (query, args) tuples.
    """

    def __init__(self, fetchrow_results: list | None = None, fetchval_results: list | None = None):
        self.fetchrow_results = list(fetchrow_results or [])
        self.fetchval_results = list(fetchval_results or [])
        self.fetchrow_calls: list[tuple] = []
        self.execute_calls: list[tuple] = []

    async def fetchrow(self, query, *args):
        self.fetchrow_calls.append((query, args))
        return self.fetchrow_results.pop(0) if self.fetchrow_results else None

    async def fetchval(self, query, *args):
        return self.fetchval_results.pop(0) if self.fetchval_results else None

    async def execute(self, query, *args):
        self.execute_calls.append((query, args))
        return "UPDATE 1"


def make_get_conn(conn: FakeConn):
    """Return an asynccontextmanager factory yielding the given FakeConn,
    suitable for patching module-level `get_conn` imports."""

    @asynccontextmanager
    async def _get_conn():
        yield conn

    return _get_conn


@pytest.fixture
def fake_conn():
    return FakeConn()
