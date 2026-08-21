"""
Tests for the YouTube connector: _distill_profile (pure function),
/youtube/profile endpoint, /youtube/analyze endpoint (mocked LLM),
and /youtube/connect 503 guard.

Uses FakeConn from conftest — no real DB or external HTTP calls.

Run:  cd server && python -m pytest tests/ -v
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.auth.deps import get_current_user_id
from app.youtube.router import _distill_profile, router as youtube_router

from .conftest import FakeConn, make_get_conn

USER_ID = UUID("00000000-0000-0000-0000-000000000007")

SAMPLE_CHANNEL = {
    "snippet": {
        "title": "Midnight Cipher",
        "description": "Exploring sound, code, and consciousness.",
        "publishedAt": "2016-09-01T00:00:00Z",
    },
    "statistics": {
        "subscriberCount": "4200",
        "videoCount": "38",
        "viewCount": "91000",
    },
}

SAMPLE_SUBSCRIPTIONS = [
    {"snippet": {"title": "3Blue1Brown", "description": "math education animated"}},
    {"snippet": {"title": "Kurzgesagt", "description": "science education explainers"}},
    {"snippet": {"title": "Lofi Girl", "description": "music study beats"}},
    {"snippet": {"title": "Linus Tech Tips", "description": "technology hardware reviews"}},
    {"snippet": {"title": "FitnessBlender", "description": "fitness workouts cardio"}},
]


def _make_app() -> FastAPI:
    app = FastAPI()
    app.include_router(youtube_router, prefix="/api/youtube")
    app.dependency_overrides[get_current_user_id] = lambda: USER_ID
    return app


# ── _distill_profile (pure function) ─────────────────────────────────────────


class TestDistillProfile:
    def test_empty_inputs_return_defaults(self):
        result = _distill_profile({}, [], 0)
        assert result["channel_name"] == ""
        assert result["top_subscriptions"] == []
        assert result["total_subscriptions"] == 0
        assert result["liked_videos_count"] == 0
        assert result["subscriber_count"] == 0
        assert result["video_count"] == 0
        assert result["view_count"] == 0

    def test_channel_name_and_description_extracted(self):
        result = _distill_profile(SAMPLE_CHANNEL, [], 0)
        assert result["channel_name"] == "Midnight Cipher"
        assert "sound" in result["channel_description"]

    def test_statistics_cast_to_int(self):
        result = _distill_profile(SAMPLE_CHANNEL, [], 0)
        assert result["subscriber_count"] == 4200
        assert result["video_count"] == 38
        assert result["view_count"] == 91000

    def test_top_subscriptions_capped_at_20(self):
        many_subs = [{"snippet": {"title": f"Channel{i}", "description": ""}} for i in range(30)]
        result = _distill_profile({}, many_subs, 0)
        assert len(result["top_subscriptions"]) <= 20

    def test_subscription_titles_collected(self):
        result = _distill_profile({}, SAMPLE_SUBSCRIPTIONS, 0)
        assert "3Blue1Brown" in result["top_subscriptions"]
        assert "Lofi Girl" in result["top_subscriptions"]

    def test_total_subscriptions_reflects_full_list(self):
        result = _distill_profile({}, SAMPLE_SUBSCRIPTIONS, 0)
        assert result["total_subscriptions"] == len(SAMPLE_SUBSCRIPTIONS)

    def test_liked_videos_count_passed_through(self):
        result = _distill_profile({}, [], 77)
        assert result["liked_videos_count"] == 77

    def test_subscription_diversity_matches_title_count(self):
        result = _distill_profile({}, SAMPLE_SUBSCRIPTIONS, 0)
        assert result["subscription_diversity"] == len(result["top_subscriptions"])

    def test_category_extraction_from_description(self):
        subs = [
            {"snippet": {"title": "MusicChannel", "description": "great music beats and songs"}},
            {"snippet": {"title": "TechChannel", "description": "technology and programming tutorials"}},
        ]
        result = _distill_profile({}, subs, 0)
        cats = result["subscription_categories"]
        assert "music" in cats
        assert "technology" in cats

    def test_description_capped_at_500_chars(self):
        long_desc = "x" * 600
        channel = {
            "snippet": {"title": "T", "description": long_desc, "publishedAt": ""},
            "statistics": {},
        }
        result = _distill_profile(channel, [], 0)
        assert len(result["channel_description"]) <= 500

    def test_missing_statistics_defaults_to_zero(self):
        channel = {"snippet": {"title": "Quiet", "description": "", "publishedAt": ""}, "statistics": {}}
        result = _distill_profile(channel, [], 0)
        assert result["subscriber_count"] == 0
        assert result["video_count"] == 0
        assert result["view_count"] == 0


# ── /youtube/profile endpoint ─────────────────────────────────────────────────


class TestYoutubeProfileEndpoint:
    def test_returns_null_when_no_vibe_vectors_row(self):
        conn = FakeConn(fetchrow_results=[None])
        app = _make_app()
        with patch("app.youtube.router.get_conn", make_get_conn(conn)):
            resp = TestClient(app).get("/api/youtube/profile")
        assert resp.status_code == 200
        assert resp.json() is None

    def test_returns_null_when_youtube_data_is_null(self):
        conn = FakeConn(fetchrow_results=[{"youtube_data": None}])
        app = _make_app()
        with patch("app.youtube.router.get_conn", make_get_conn(conn)):
            resp = TestClient(app).get("/api/youtube/profile")
        assert resp.status_code == 200
        assert resp.json() is None

    def test_returns_parsed_dict_when_data_is_json_string(self):
        stored = json.dumps({"channel_name": "Midnight Cipher", "subscriber_count": 4200})
        conn = FakeConn(fetchrow_results=[{"youtube_data": stored}])
        app = _make_app()
        with patch("app.youtube.router.get_conn", make_get_conn(conn)):
            resp = TestClient(app).get("/api/youtube/profile")
        assert resp.status_code == 200
        body = resp.json()
        assert body["channel_name"] == "Midnight Cipher"
        assert body["subscriber_count"] == 4200

    def test_returns_dict_passthrough_when_already_dict(self):
        stored = {"channel_name": "Midnight Cipher", "liked_videos_count": 77}
        conn = FakeConn(fetchrow_results=[{"youtube_data": stored}])
        app = _make_app()
        with patch("app.youtube.router.get_conn", make_get_conn(conn)):
            resp = TestClient(app).get("/api/youtube/profile")
        assert resp.status_code == 200
        assert resp.json()["liked_videos_count"] == 77


# ── /youtube/analyze endpoint ─────────────────────────────────────────────────


class TestYoutubeAnalyzeEndpoint:
    def test_404_when_no_vibe_vectors_row(self):
        conn = FakeConn(fetchrow_results=[None])
        app = _make_app()
        with patch("app.youtube.router.get_conn", make_get_conn(conn)):
            resp = TestClient(app).get("/api/youtube/analyze")
        assert resp.status_code == 404

    def test_404_when_youtube_data_is_null(self):
        conn = FakeConn(fetchrow_results=[{"youtube_data": None}])
        app = _make_app()
        with patch("app.youtube.router.get_conn", make_get_conn(conn)):
            resp = TestClient(app).get("/api/youtube/analyze")
        assert resp.status_code == 404

    def test_200_with_narrative_when_data_present(self):
        stored = json.dumps({"channel_name": "Midnight Cipher", "top_subscriptions": ["3Blue1Brown"]})
        conn = FakeConn(fetchrow_results=[{"youtube_data": stored}])
        app = _make_app()
        with (
            patch("app.youtube.router.get_conn", make_get_conn(conn)),
            patch("app.youtube.router.chat_completion", new=AsyncMock(return_value="You consume to become.")),
        ):
            resp = TestClient(app).get("/api/youtube/analyze")
        assert resp.status_code == 200
        assert resp.json()["narrative"] == "You consume to become."


# ── /youtube/connect 503 guard ────────────────────────────────────────────────


class TestYoutubeConnectEndpoint:
    def test_503_when_google_client_id_not_configured(self):
        """Missing GOOGLE_CLIENT_ID → 503 before any token validation or DB call."""
        app = _make_app()
        with patch("app.youtube.router.get_settings") as mock_settings:
            mock_settings.return_value.google_client_id = None
            resp = TestClient(app).get("/api/youtube/connect")
        assert resp.status_code == 503
        assert "not configured" in resp.json()["detail"].lower()
