"""
Tests for the Reddit connector: _distill_profile (pure function),
/reddit/profile endpoint, /reddit/analyze endpoint (mocked LLM),
and /reddit/connect 503 guard.

Uses FakeConn from conftest — no real DB or external HTTP calls.

Run:  cd server && python -m pytest tests/ -v
"""

from __future__ import annotations

import json
import time
from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.auth.deps import get_current_user_id
from app.reddit.router import _distill_profile, router as reddit_router

from .conftest import FakeConn, make_get_conn

USER_ID = UUID("00000000-0000-0000-0000-000000000008")

SAMPLE_ME = {
    "name": "signal_ghost",
    "link_karma": 310,
    "comment_karma": 2900,
    "created_utc": time.time() - (3 * 365 * 86400),  # 3 years old
}

SAMPLE_SUBREDDITS = [
    {"data": {"display_name": "MachineLearning", "subscribers": 3_000_000}},
    {"data": {"display_name": "indiegaming", "subscribers": 400_000}},
    {"data": {"display_name": "LofiHipHop", "subscribers": 120_000}},
]

SAMPLE_COMMENTS = [
    {"data": {"subreddit": "MachineLearning", "created_utc": time.time() - 3600}},
    {"data": {"subreddit": "MachineLearning", "created_utc": time.time() - 7200}},
    {"data": {"subreddit": "indiegaming", "created_utc": time.time() - 10800}},
]

SAMPLE_TROPHIES = [
    {"data": {"name": "Two-Year Club"}},
    {"data": {"name": "Verified Email"}},
]


def _make_app() -> FastAPI:
    app = FastAPI()
    app.include_router(reddit_router, prefix="/api/reddit")
    app.dependency_overrides[get_current_user_id] = lambda: USER_ID
    return app


# ── _distill_profile (pure function) ─────────────────────────────────────────


class TestDistillProfile:
    def test_empty_inputs_return_defaults(self):
        result = _distill_profile({}, [], [], [], [])
        assert result["username"] == ""
        assert result["total_karma"] == 0
        assert result["account_age_days"] == 0
        assert result["top_subreddits"] == []
        assert result["comment_subreddits"] == []
        assert result["trophies"] == []
        assert result["subreddit_diversity"] == 0

    def test_karma_totals_and_ratio(self):
        result = _distill_profile(SAMPLE_ME, [], [], [], [])
        assert result["link_karma"] == 310
        assert result["comment_karma"] == 2900
        assert result["total_karma"] == 3210
        expected_ratio = round(2900 / 3210, 3)
        assert result["comment_karma_ratio"] == expected_ratio

    def test_karma_ratio_none_when_zero_karma(self):
        zero_karma_me = {"name": "lurker", "link_karma": 0, "comment_karma": 0, "created_utc": 0}
        result = _distill_profile(zero_karma_me, [], [], [], [])
        assert result["comment_karma_ratio"] is None

    def test_account_age_computed(self):
        result = _distill_profile(SAMPLE_ME, [], [], [], [])
        assert result["account_age_days"] > 1000  # ~3 years ≈ 1095 days

    def test_zero_created_utc_gives_zero_age(self):
        me = {"name": "ghost", "link_karma": 0, "comment_karma": 0, "created_utc": 0}
        result = _distill_profile(me, [], [], [], [])
        assert result["account_age_days"] == 0

    def test_top_subreddits_sorted_by_subscribers_descending(self):
        result = _distill_profile({}, SAMPLE_SUBREDDITS, [], [], [])
        names = [s["name"] for s in result["top_subreddits"]]
        assert names[0] == "MachineLearning"
        assert names[1] == "indiegaming"

    def test_top_subreddits_capped_at_30(self):
        many_subs = [{"data": {"display_name": f"r{i}", "subscribers": i}} for i in range(40)]
        result = _distill_profile({}, many_subs, [], [], [])
        assert len(result["top_subreddits"]) <= 30

    def test_comment_subreddits_counted_by_frequency(self):
        result = _distill_profile({}, [], SAMPLE_COMMENTS, [], [])
        comment_subs = {s["name"]: s["count"] for s in result["comment_subreddits"]}
        assert comment_subs.get("MachineLearning") == 2
        assert comment_subs.get("indiegaming") == 1

    def test_active_hours_extracted_from_comments(self):
        result = _distill_profile({}, [], SAMPLE_COMMENTS, [], [])
        assert len(result["active_hours"]) > 0
        total = sum(result["active_hours"].values())
        assert total == len(SAMPLE_COMMENTS)

    def test_trophies_extracted_by_name(self):
        result = _distill_profile({}, [], [], [], SAMPLE_TROPHIES)
        assert "Two-Year Club" in result["trophies"]
        assert "Verified Email" in result["trophies"]
        assert result["trophy_count"] == 2

    def test_trophies_capped_at_10(self):
        many_trophies = [{"data": {"name": f"Trophy{i}"}} for i in range(15)]
        result = _distill_profile({}, [], [], [], many_trophies)
        assert len(result["trophies"]) <= 10

    def test_subreddit_diversity_union_of_sub_and_comment_sources(self):
        result = _distill_profile({}, SAMPLE_SUBREDDITS, SAMPLE_COMMENTS, [], [])
        # MachineLearning appears in both; union should not double-count
        unique_names = {"MachineLearning", "indiegaming", "LofiHipHop"}
        assert result["subreddit_diversity"] == len(unique_names)

    def test_recent_comments_and_saved_counts_recorded(self):
        result = _distill_profile({}, [], SAMPLE_COMMENTS, [{"id": 1}, {"id": 2}], [])
        assert result["recent_comments_analyzed"] == len(SAMPLE_COMMENTS)
        assert result["saved_posts_analyzed"] == 2

    def test_username_extracted(self):
        result = _distill_profile(SAMPLE_ME, [], [], [], [])
        assert result["username"] == "signal_ghost"


# ── /reddit/profile endpoint ──────────────────────────────────────────────────


class TestRedditProfileEndpoint:
    def test_returns_null_when_no_vibe_vectors_row(self):
        conn = FakeConn(fetchrow_results=[None])
        app = _make_app()
        with patch("app.reddit.router.get_conn", make_get_conn(conn)):
            resp = TestClient(app).get("/api/reddit/profile")
        assert resp.status_code == 200
        assert resp.json() is None

    def test_returns_null_when_reddit_data_is_null(self):
        conn = FakeConn(fetchrow_results=[{"reddit_data": None}])
        app = _make_app()
        with patch("app.reddit.router.get_conn", make_get_conn(conn)):
            resp = TestClient(app).get("/api/reddit/profile")
        assert resp.status_code == 200
        assert resp.json() is None

    def test_returns_parsed_dict_when_data_is_json_string(self):
        stored = json.dumps({"username": "signal_ghost", "total_karma": 3210})
        conn = FakeConn(fetchrow_results=[{"reddit_data": stored}])
        app = _make_app()
        with patch("app.reddit.router.get_conn", make_get_conn(conn)):
            resp = TestClient(app).get("/api/reddit/profile")
        assert resp.status_code == 200
        body = resp.json()
        assert body["username"] == "signal_ghost"
        assert body["total_karma"] == 3210

    def test_returns_dict_passthrough_when_already_dict(self):
        stored = {"username": "signal_ghost", "subreddit_diversity": 12}
        conn = FakeConn(fetchrow_results=[{"reddit_data": stored}])
        app = _make_app()
        with patch("app.reddit.router.get_conn", make_get_conn(conn)):
            resp = TestClient(app).get("/api/reddit/profile")
        assert resp.status_code == 200
        assert resp.json()["subreddit_diversity"] == 12


# ── /reddit/analyze endpoint ──────────────────────────────────────────────────


class TestRedditAnalyzeEndpoint:
    def test_404_when_no_vibe_vectors_row(self):
        conn = FakeConn(fetchrow_results=[None])
        app = _make_app()
        with patch("app.reddit.router.get_conn", make_get_conn(conn)):
            resp = TestClient(app).get("/api/reddit/analyze")
        assert resp.status_code == 404

    def test_404_when_reddit_data_is_null(self):
        conn = FakeConn(fetchrow_results=[{"reddit_data": None}])
        app = _make_app()
        with patch("app.reddit.router.get_conn", make_get_conn(conn)):
            resp = TestClient(app).get("/api/reddit/analyze")
        assert resp.status_code == 404

    def test_200_with_narrative_when_data_present(self):
        stored = json.dumps({"username": "signal_ghost", "top_subreddits": [{"name": "MachineLearning"}]})
        conn = FakeConn(fetchrow_results=[{"reddit_data": stored}])
        app = _make_app()
        with (
            patch("app.reddit.router.get_conn", make_get_conn(conn)),
            patch("app.reddit.router.chat_completion", new=AsyncMock(return_value="You watch to belong.")),
        ):
            resp = TestClient(app).get("/api/reddit/analyze")
        assert resp.status_code == 200
        assert resp.json()["narrative"] == "You watch to belong."


# ── /reddit/connect 503 guard ─────────────────────────────────────────────────


class TestRedditConnectEndpoint:
    def test_503_when_reddit_client_id_not_configured(self):
        """Missing REDDIT_CLIENT_ID → 503 before any token validation or DB call."""
        app = _make_app()
        with patch("app.reddit.router.get_settings") as mock_settings:
            mock_settings.return_value.reddit_client_id = None
            resp = TestClient(app).get("/api/reddit/connect")
        assert resp.status_code == 503
        assert "not configured" in resp.json()["detail"].lower()
