"""Tests for POST /api/analytics/event rate limiting (60/minute)."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.auth.deps import get_current_user_id
from app.main import app
from app.ratelimit import limiter

FAKE_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture(autouse=True)
def reset_limiter():
    """Clear in-memory rate-limit counters before each test."""
    limiter._storage.reset()
    yield


@pytest.fixture(autouse=True)
def override_auth():
    """Bypass JWT auth so rate-limit tests can reach the handler."""
    app.dependency_overrides[get_current_user_id] = lambda: FAKE_USER_ID
    yield
    app.dependency_overrides.pop(get_current_user_id, None)


def _fake_conn():
    conn = MagicMock()
    conn.__aenter__ = AsyncMock(return_value=conn)
    conn.__aexit__ = AsyncMock(return_value=False)
    conn.execute = AsyncMock(return_value=None)
    return conn


class TestAnalyticsEventRateLimit:
    def test_first_attempt_not_rate_limited(self):
        client = TestClient(app, raise_server_exceptions=False)
        with patch("app.analytics.router.get_conn", return_value=_fake_conn()):
            resp = client.post("/api/analytics/event", json={"event": "journal_session_started"})
        assert resp.status_code != 429

    def test_61st_attempt_returns_429(self):
        client = TestClient(app, raise_server_exceptions=False)
        with patch("app.analytics.router.get_conn", return_value=_fake_conn()):
            for _ in range(60):
                client.post("/api/analytics/event", json={"event": "journal_session_started"})
            resp = client.post("/api/analytics/event", json={"event": "journal_session_started"})
        assert resp.status_code == 429

    def test_429_has_retry_after_header(self):
        client = TestClient(app, raise_server_exceptions=False)
        with patch("app.analytics.router.get_conn", return_value=_fake_conn()):
            for _ in range(60):
                client.post("/api/analytics/event", json={"event": "journal_session_started"})
            resp = client.post("/api/analytics/event", json={"event": "journal_session_started"})
        assert resp.status_code == 429
        assert "retry-after" in {k.lower() for k in resp.headers}
