"""
Tests for the Steam connector.

Run:  cd server && python -m pytest tests/test_steam_connector.py -v
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.auth.deps import get_current_user_id
from app.steam.router import router as steam_router, _distill_profile

from .conftest import FakeConn, make_get_conn

USER_ID = "11111111-1111-1111-1111-111111111111"


def _make_app() -> FastAPI:
    app = FastAPI()
    app.include_router(steam_router, prefix="/api/steam")
    app.dependency_overrides[get_current_user_id] = lambda: USER_ID
    return app


def _game(name: str, playtime_forever: int, playtime_2weeks: int = 0) -> dict:
    """Build a minimal Steam game dict (playtime in minutes, as Steam API returns)."""
    return {"name": name, "playtime_forever": playtime_forever, "playtime_2weeks": playtime_2weeks}


# ── _distill_profile ─────────────────────────────────────────────────────

class TestDistillProfile:
    def test_empty_inputs(self):
        result = _distill_profile("76561198000000001", "GhostPlayer", [], [], 0)
        assert result["steam_id"] == "76561198000000001"
        assert result["persona_name"] == "GhostPlayer"
        assert result["game_count"] == 0
        assert result["recent_2week_hours"] == 0
        assert result["recent_titles"] == []
        assert result["total_lifetime_hours"] == 0
        assert result["top_games"] == []
        assert result["heavy_session_hours"] == 0

    def test_recent_hours_converts_minutes_to_hours(self):
        recent = [
            _game("Half-Life", 0, playtime_2weeks=120),
            _game("Portal", 0, playtime_2weeks=60),
        ]
        result = _distill_profile("id", "P", recent, [], 2)
        assert result["recent_2week_hours"] == 3.0  # (120 + 60) / 60

    def test_recent_titles_capped_at_ten(self):
        recent = [_game(f"Game{i}", 0, playtime_2weeks=30) for i in range(12)]
        result = _distill_profile("id", "P", recent, [], 12)
        assert len(result["recent_titles"]) == 10

    def test_recent_titles_fallback_name_when_key_missing(self):
        recent = [{"playtime_2weeks": 60}]  # no "name" key
        result = _distill_profile("id", "P", recent, [], 1)
        assert result["recent_titles"] == ["Unknown"]

    def test_total_lifetime_hours_converts_minutes(self):
        owned = [_game("CS:GO", 6000), _game("Dota 2", 12000)]  # 100h + 200h
        result = _distill_profile("id", "P", [], owned, 2)
        assert result["total_lifetime_hours"] == 300.0

    def test_top_games_sorted_descending_by_playtime(self):
        owned = [
            _game("Portal", 600),
            _game("Half-Life", 3000),
            _game("CS:GO", 1200),
        ]
        result = _distill_profile("id", "P", [], owned, 3)
        names = [g["name"] for g in result["top_games"]]
        assert names == ["Half-Life", "CS:GO", "Portal"]

    def test_top_games_capped_at_ten(self):
        owned = [_game(f"Game{i}", (10 - i) * 100) for i in range(15)]
        result = _distill_profile("id", "P", [], owned, 15)
        assert len(result["top_games"]) == 10

    def test_top_games_hours_field_converted_from_minutes(self):
        owned = [_game("Skyrim", 6000)]  # 6000 min = 100 h
        result = _distill_profile("id", "P", [], owned, 1)
        assert result["top_games"][0]["hours"] == 100.0

    def test_heavy_session_hours_sums_only_top_five(self):
        # 6 games sorted desc: 3600, 3000, 2400, 1800, 1200, 600 minutes
        # top-5 sum = 12000 min = 200 h
        owned = [_game(f"Game{i}", (6 - i) * 600) for i in range(6)]
        result = _distill_profile("id", "P", [], owned, 6)
        assert result["heavy_session_hours"] == 200.0

    def test_heavy_session_hours_zero_when_no_owned_games(self):
        result = _distill_profile("id", "P", [], [], 0)
        assert result["heavy_session_hours"] == 0

    def test_game_count_passed_through(self):
        result = _distill_profile("id", "P", [], [], 247)
        assert result["game_count"] == 247


# ── GET /steam/connect ───────────────────────────────────────────────

class TestSteamConnectEndpoint:
    def test_503_when_steam_api_key_not_set(self):
        mock_settings = MagicMock()
        mock_settings.steam_api_key = ""
        with patch("app.steam.router.get_settings", return_value=mock_settings):
            r = TestClient(_make_app(), raise_server_exceptions=False).get("/api/steam/connect")
        assert r.status_code == 503

    def test_returns_auth_url_when_configured(self):
        mock_settings = MagicMock()
        mock_settings.steam_api_key = "testkey123"
        mock_settings.steam_redirect_uri = "https://channelzero.onrender.com/api/steam/callback"
        mock_settings.cors_origin_list = ["https://channelzero.vercel.app"]
        mock_settings.jwt_secret = "testsecret"
        with patch("app.steam.router.get_settings", return_value=mock_settings):
            r = TestClient(_make_app()).get("/api/steam/connect")
        assert r.status_code == 200
        body = r.json()
        assert "auth_url" in body
        assert "steamcommunity.com/openid" in body["auth_url"]


# ── GET /steam/analyze ──────────────────────────────────────────────

class TestSteamAnalyzeEndpoint:
    def test_404_when_no_row(self):
        conn = FakeConn()  # empty fetchrow_results → fetchrow returns None
        with patch("app.steam.router.get_conn", make_get_conn(conn)):
            r = TestClient(_make_app(), raise_server_exceptions=False).get("/api/steam/analyze")
        assert r.status_code == 404

    def test_404_when_steam_data_null(self):
        conn = FakeConn(fetchrow_results=[{"steam_data": None}])
        with patch("app.steam.router.get_conn", make_get_conn(conn)):
            r = TestClient(_make_app(), raise_server_exceptions=False).get("/api/steam/analyze")
        assert r.status_code == 404

    def test_200_with_mocked_narrative(self):
        payload = {
            "steam_id": "76561198000000001",
            "persona_name": "GhostPlayer",
            "game_count": 247,
            "recent_2week_hours": 8.5,
            "recent_titles": ["Elden Ring"],
            "total_lifetime_hours": 3200.0,
            "top_games": [{"name": "Elden Ring", "hours": 450.0}],
            "heavy_session_hours": 890.0,
        }
        conn = FakeConn(fetchrow_results=[{"steam_data": json.dumps(payload)}])
        with patch("app.steam.router.get_conn", make_get_conn(conn)), \
             patch("app.steam.router.chat_completion",
                   new=AsyncMock(return_value="You inhabit worlds built for mastery.")):
            r = TestClient(_make_app(), raise_server_exceptions=False).get("/api/steam/analyze")
        assert r.status_code == 200
        assert r.json()["narrative"] == "You inhabit worlds built for mastery."
