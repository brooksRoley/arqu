"""Tests for /auth/login and /auth/register rate limiting.

Requires the same env vars as other server tests (DATABASE_URL, JWT_SECRET,
SERVER_ENCRYPTION_KEY). The TestClient does not trigger the lifespan (no DB
pool is opened), so these tests only exercise the rate-limiting middleware.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from server.app.main import app
from server.app.ratelimit import limiter


@pytest.fixture(autouse=True)
def reset_limiter():
    """Clear in-memory rate-limit counters before each test."""
    limiter._storage.reset()
    yield


def _fake_conn():
    conn = MagicMock()
    conn.__aenter__ = AsyncMock(return_value=conn)
    conn.__aexit__ = AsyncMock(return_value=False)
    conn.fetchval = AsyncMock(return_value=None)
    conn.fetchrow = AsyncMock(return_value=None)
    conn.execute = AsyncMock(return_value=None)
    return conn


class TestLoginRateLimit:
    def test_first_attempt_not_rate_limited(self):
        client = TestClient(app, raise_server_exceptions=False)
        with patch("server.app.auth.router.get_conn", return_value=_fake_conn()):
            resp = client.post("/api/auth/login", json={"email": "a@b.com", "password": "pw"})
        assert resp.status_code != 429

    def test_sixth_attempt_returns_429(self):
        client = TestClient(app, raise_server_exceptions=False)
        with patch("server.app.auth.router.get_conn", return_value=_fake_conn()):
            for _ in range(5):
                client.post("/api/auth/login", json={"email": "x@y.com", "password": "p"})
            resp = client.post("/api/auth/login", json={"email": "x@y.com", "password": "p"})
        assert resp.status_code == 429

    def test_429_response_has_retry_after_header(self):
        client = TestClient(app, raise_server_exceptions=False)
        with patch("server.app.auth.router.get_conn", return_value=_fake_conn()):
            for _ in range(5):
                client.post("/api/auth/login", json={"email": "z@z.com", "password": "p"})
            resp = client.post("/api/auth/login", json={"email": "z@z.com", "password": "p"})
        assert resp.status_code == 429
        assert "retry-after" in resp.headers or "Retry-After" in resp.headers


class TestRegisterRateLimit:
    def test_first_attempt_not_rate_limited(self):
        client = TestClient(app, raise_server_exceptions=False)
        with patch("server.app.auth.router.get_conn", return_value=_fake_conn()):
            resp = client.post(
                "/api/auth/register",
                json={"email": "new@b.com", "password": "pw123", "display_name": "New"},
            )
        assert resp.status_code != 429

    def test_fourth_attempt_returns_429(self):
        client = TestClient(app, raise_server_exceptions=False)
        with patch("server.app.auth.router.get_conn", return_value=_fake_conn()):
            for _ in range(3):
                client.post(
                    "/api/auth/register",
                    json={"email": "x@b.com", "password": "pw", "display_name": "X"},
                )
            resp = client.post(
                "/api/auth/register",
                json={"email": "x@b.com", "password": "pw", "display_name": "X"},
            )
        assert resp.status_code == 429
