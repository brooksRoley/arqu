"""
Tests for /api/strava — profile retrieval, psychoanalysis endpoint, and
the _distill_profile pure function.

Covers:
- GET /strava/profile: happy path (JSON string + dict), no row, null data
- GET /strava/analyze: happy path, no data → 404, null data → 404
- _distill_profile: activity aggregation, heartrate logic, empty input

Run:  cd server && python -m pytest tests/test_strava.py -v
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.auth.deps import get_current_user_id
from app.strava.router import _distill_profile, router as strava_router

from .conftest import FakeConn, make_get_conn

USER_ID = UUID("00000000-0000-0000-0000-000000000002")

_SAMPLE_PROFILE = {
    "athlete_name": "Test Runner",
    "activity_types": {"Run": 20, "Ride": 5},
    "recent_count": 25,
    "total_elevation_m": 1500.0,
    "total_distance_km": 300.0,
    "total_moving_hours": 24.0,
    "avg_heartrate": 142.0,
    "max_heartrate": 178.0,
    "all_time_runs": 200,
    "all_time_run_distance_km": 1200.0,
    "all_time_rides": 30,
    "all_time_ride_distance_km": 600.0,
}


def _make_app() -> FastAPI:
    app = FastAPI()
    app.include_router(strava_router, prefix="/api/strava")
    app.dependency_overrides[get_current_user_id] = lambda: USER_ID
    return app


class TestStravaProfile:
    """GET /strava/profile"""

    def test_returns_profile_when_data_is_json_string(self):
        conn = FakeConn(fetchrow_results=[{"strava_data": json.dumps(_SAMPLE_PROFILE)}])
        with patch("app.strava.router.get_conn", make_get_conn(conn)):
            resp = TestClient(_make_app()).get("/api/strava/profile")
        assert resp.status_code == 200
        data = resp.json()
        assert data["athlete_name"] == "Test Runner"
        assert data["activity_types"]["Run"] == 20

    def test_returns_profile_when_data_is_dict(self):
        """strava_data may arrive as a dict (asyncpg JSONB auto-decodes)."""
        conn = FakeConn(fetchrow_results=[{"strava_data": _SAMPLE_PROFILE}])
        with patch("app.strava.router.get_conn", make_get_conn(conn)):
            resp = TestClient(_make_app()).get("/api/strava/profile")
        assert resp.status_code == 200
        assert resp.json()["athlete_name"] == "Test Runner"

    def test_returns_null_when_no_row(self):
        conn = FakeConn(fetchrow_results=[None])
        with patch("app.strava.router.get_conn", make_get_conn(conn)):
            resp = TestClient(_make_app()).get("/api/strava/profile")
        assert resp.status_code == 200
        assert resp.json() is None

    def test_returns_null_when_row_has_null_data(self):
        conn = FakeConn(fetchrow_results=[{"strava_data": None}])
        with patch("app.strava.router.get_conn", make_get_conn(conn)):
            resp = TestClient(_make_app()).get("/api/strava/profile")
        assert resp.status_code == 200
        assert resp.json() is None


class TestStravaAnalyze:
    """GET /strava/analyze"""

    def _analyze_patches(self, conn: FakeConn, narrative: str = "narrative"):
        """Context manager applying the three patches needed for /analyze."""
        return (
            patch("app.strava.router.get_conn", make_get_conn(conn)),
            patch("app.strava.router.get_settings", return_value=MagicMock()),
            patch("app.strava.router.chat_completion", new=AsyncMock(return_value=narrative)),
        )

    def test_returns_narrative_for_connected_user(self):
        conn = FakeConn(fetchrow_results=[{"strava_data": json.dumps(_SAMPLE_PROFILE)}])
        mock_narrative = "You run to outpace your thoughts."
        with patch("app.strava.router.get_conn", make_get_conn(conn)), \
             patch("app.strava.router.get_settings", return_value=MagicMock()), \
             patch("app.strava.router.chat_completion", new=AsyncMock(return_value=mock_narrative)):
            resp = TestClient(_make_app()).get("/api/strava/analyze")
        assert resp.status_code == 200
        assert resp.json()["narrative"] == mock_narrative

    def test_chat_completion_called_with_somatic_prompt(self):
        """The LLM prompt must include key somatic metrics from the profile."""
        conn = FakeConn(fetchrow_results=[{"strava_data": json.dumps(_SAMPLE_PROFILE)}])
        captured: list[str] = []

        async def _capture(prompt: str) -> str:
            captured.append(prompt)
            return "ok"

        with patch("app.strava.router.get_conn", make_get_conn(conn)), \
             patch("app.strava.router.get_settings", return_value=MagicMock()), \
             patch("app.strava.router.chat_completion", side_effect=_capture):
            TestClient(_make_app()).get("/api/strava/analyze")

        assert captured, "chat_completion was not called"
        prompt = captured[0]
        assert "300" in prompt  # total_distance_km
        assert "1500" in prompt  # total_elevation_m

    def test_404_when_no_row(self):
        conn = FakeConn(fetchrow_results=[None])
        with patch("app.strava.router.get_conn", make_get_conn(conn)), \
             patch("app.strava.router.get_settings", return_value=MagicMock()), \
             patch("app.strava.router.chat_completion", new=AsyncMock(return_value="x")):
            resp = TestClient(_make_app()).get("/api/strava/analyze")
        assert resp.status_code == 404

    def test_404_when_row_has_null_data(self):
        conn = FakeConn(fetchrow_results=[{"strava_data": None}])
        with patch("app.strava.router.get_conn", make_get_conn(conn)), \
             patch("app.strava.router.get_settings", return_value=MagicMock()), \
             patch("app.strava.router.chat_completion", new=AsyncMock(return_value="x")):
            resp = TestClient(_make_app()).get("/api/strava/analyze")
        assert resp.status_code == 404


class TestDistillProfile:
    """_distill_profile — pure function, no mocking required."""

    def test_aggregates_activity_types_and_distance(self):
        athlete = {"firstname": "Jane", "lastname": "Doe"}
        activities = [
            {"type": "Run", "distance": 10000, "moving_time": 3600, "total_elevation_gain": 100},
            {"type": "Run", "distance": 5000, "moving_time": 1800, "total_elevation_gain": 50},
            {"type": "Ride", "distance": 20000, "moving_time": 3600, "total_elevation_gain": 200},
        ]
        stats = {
            "all_run_totals": {"count": 150, "distance": 1_200_000},
            "all_ride_totals": {"count": 40, "distance": 800_000},
        }
        result = _distill_profile(athlete, activities, stats)

        assert result["athlete_name"] == "Jane Doe"
        assert result["activity_types"] == {"Run": 2, "Ride": 1}
        assert result["recent_count"] == 3
        assert result["total_distance_km"] == pytest.approx(35.0)
        assert result["total_moving_hours"] == pytest.approx(2.5)
        assert result["total_elevation_m"] == pytest.approx(350.0)
        assert result["all_time_runs"] == 150
        assert result["all_time_run_distance_km"] == pytest.approx(1200.0)
        assert result["all_time_rides"] == 40
        assert result["all_time_ride_distance_km"] == pytest.approx(800.0)

    def test_heartrate_absent_when_no_activities_report_it(self):
        activities = [
            {"type": "Run", "distance": 5000, "moving_time": 1800, "total_elevation_gain": 50},
        ]
        result = _distill_profile({}, activities, {})
        assert result["avg_heartrate"] is None
        assert result["max_heartrate"] is None

    def test_heartrate_averaged_across_activities(self):
        activities = [
            {"type": "Run", "distance": 10000, "moving_time": 3600,
             "total_elevation_gain": 0, "average_heartrate": 140.0},
            {"type": "Run", "distance": 10000, "moving_time": 3600,
             "total_elevation_gain": 0, "average_heartrate": 160.0},
        ]
        result = _distill_profile({}, activities, {})
        assert result["avg_heartrate"] == pytest.approx(150.0)
        assert result["max_heartrate"] == pytest.approx(160.0)

    def test_empty_activities_list(self):
        result = _distill_profile({"firstname": "Empty", "lastname": ""}, [], {})
        assert result["recent_count"] == 0
        assert result["total_distance_km"] == 0.0
        assert result["activity_types"] == {}
        assert result["avg_heartrate"] is None

    def test_athlete_name_strips_whitespace_for_anonymous(self):
        result = _distill_profile({}, [], {})
        assert result["athlete_name"] == ""
