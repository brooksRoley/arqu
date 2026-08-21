"""Tests for POST /api/portrait/generate rate limiting (5/hour)."""
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


def _mock_portrait_data():
    data = MagicMock()
    data.connected = ["spotify", "github"]
    data.portrait = None
    data.generated_at = None
    data.source_providers = []
    return data


class TestPortraitGenerateRateLimit:
    def test_first_attempt_not_rate_limited(self):
        client = TestClient(app, raise_server_exceptions=False)
        with patch("app.portrait.router.fetch_portrait_data", AsyncMock(return_value=_mock_portrait_data())), \
             patch("app.portrait.router.llm_configured", return_value=False):
            resp = client.post("/api/portrait/generate")
        assert resp.status_code != 429

    def test_sixth_attempt_returns_429(self):
        client = TestClient(app, raise_server_exceptions=False)
        with patch("app.portrait.router.fetch_portrait_data", AsyncMock(return_value=_mock_portrait_data())), \
             patch("app.portrait.router.llm_configured", return_value=False):
            for _ in range(5):
                client.post("/api/portrait/generate")
            resp = client.post("/api/portrait/generate")
        assert resp.status_code == 429

    def test_429_has_retry_after_header(self):
        client = TestClient(app, raise_server_exceptions=False)
        with patch("app.portrait.router.fetch_portrait_data", AsyncMock(return_value=_mock_portrait_data())), \
             patch("app.portrait.router.llm_configured", return_value=False):
            for _ in range(5):
                client.post("/api/portrait/generate")
            resp = client.post("/api/portrait/generate")
        assert resp.status_code == 429
        assert "retry-after" in {k.lower() for k in resp.headers}
