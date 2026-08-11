"""
Tests for the Letterboxd connector: _distill_profile (pure function),
/letterboxd/profile endpoint, /letterboxd/analyze endpoint (mocked LLM),
/letterboxd/connect 503 guard, and /letterboxd/ingest flow (mocked httpx).

Uses FakeConn from conftest — no real DB or external HTTP calls.

Run:  cd server && python -m pytest tests/test_letterboxd_connector.py -v
"""

from __future__ import annotations

import json
from unittest.mock import ANY, AsyncMock, MagicMock, patch
from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.auth.deps import get_current_user_id
from app.letterboxd.router import (
    _distill_profile,
    router as letterboxd_router,
)

from .conftest import FakeConn, make_get_conn

USER_ID = UUID("00000000-0000-0000-0000-000000000004")

SAMPLE_ENTRIES = [
    {"film": {"name": "Stalker"}, "rating": 5.0},
    {"film": {"name": "Solaris"}, "rating": 4.5},
    {"film": {"name": "Persona"}, "rating": 4.0},
    {"film": {"name": "Come and See"}, "rating": None},  # watched, unrated
    {"film": {"name": "Mirror"}, "rating": 5.0},
]

SAMPLE_WATCHLIST = [
    {"film": {"name": "Andrei Rublev"}},
    {"film": {"name": "The Sacrifice"}},
    {"film": {"name": "Nostalghia"}},
]


def _make_app() -> FastAPI:
    app = FastAPI()
    app.include_router(letterboxd_router, prefix="/api/letterboxd")
    app.dependency_overrides[get_current_user_id] = lambda: USER_ID
    return app


def _mock_resp(status_code: int, data: dict) -> MagicMock:
    m = MagicMock()
    m.status_code = status_code
    m.json.return_value = data
    return m


def _make_async_client(get_side_effect):
    """Build a MagicMock replacement for httpx.AsyncClient supporting
    `async with httpx.AsyncClient(...) as client:` and awaited client.get()."""
    client = AsyncMock()
    client.get.side_effect = get_side_effect
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=client)
    ctx.__aexit__ = AsyncMock(return_value=False)
    factory = MagicMock(return_value=ctx)
    return factory, client


# ── _distill_profile (pure function) ─────────────────────────────────────────


class TestDistillProfile:
    def test_empty_inputs_return_defaults(self):
        result = _distill_profile("ghost", [], [])
        assert result["username"] == "ghost"
        assert result["diary_count"] == 0
        assert result["recent_films"] == []
        assert result["avg_rating"] is None
        assert result["watchlist_sample"] == []
        assert result["ratings_given"] == 0

    def test_username_passthrough(self):
        result = _distill_profile("cinephile", SAMPLE_ENTRIES, SAMPLE_WATCHLIST)
        assert result["username"] == "cinephile"

    def test_diary_count_equals_number_of_entries(self):
        result = _distill_profile("cinephile", SAMPLE_ENTRIES, [])
        assert result["diary_count"] == len(SAMPLE_ENTRIES)

    def test_recent_films_collects_titles_in_order(self):
        result = _distill_profile("cinephile", SAMPLE_ENTRIES, [])
        assert result["recent_films"][0] == "Stalker"
        assert "Come and See" in result["recent_films"]

    def test_recent_films_capped_at_fifteen(self):
        many = [{"film": {"name": f"Film{i}"}, "rating": 3.0} for i in range(25)]
        result = _distill_profile("cinephile", many, [])
        assert len(result["recent_films"]) == 15

    def test_avg_rating_computed_over_non_null_ratings(self):
        # ratings present: 5.0, 4.5, 4.0, 5.0 (None excluded) → 18.5 / 4 = 4.62
        result = _distill_profile("cinephile", SAMPLE_ENTRIES, [])
        assert result["avg_rating"] == round((5.0 + 4.5 + 4.0 + 5.0) / 4, 2)

    def test_ratings_given_excludes_none(self):
        result = _distill_profile("cinephile", SAMPLE_ENTRIES, [])
        assert result["ratings_given"] == 4  # 5 entries, one unrated

    def test_watchlist_sample_capped_at_ten_and_pulls_names(self):
        big_watchlist = [{"film": {"name": f"WL{i}"}} for i in range(20)]
        result = _distill_profile("cinephile", [], big_watchlist)
        assert len(result["watchlist_sample"]) == 10
        assert result["watchlist_sample"][0] == "WL0"

    def test_missing_film_name_falls_back_to_unknown(self):
        entries = [{"film": {}, "rating": 3.0}, {"rating": 2.0}]
        result = _distill_profile("cinephile", entries, [{}])
        assert result["recent_films"] == ["Unknown", "Unknown"]
        assert result["watchlist_sample"] == ["Unknown"]


# ── /letterboxd/profile endpoint ──────────────────────────────────────────────


class TestLetterboxdProfileEndpoint:
    def test_returns_null_when_no_vibe_vectors_row(self):
        conn = FakeConn(fetchrow_results=[None])
        app = _make_app()
        with patch("app.letterboxd.router.get_conn", make_get_conn(conn)):
            resp = TestClient(app).get("/api/letterboxd/profile")
        assert resp.status_code == 200
        assert resp.json() is None

    def test_returns_null_when_letterboxd_data_is_null(self):
        conn = FakeConn(fetchrow_results=[{"letterboxd_data": None}])
        app = _make_app()
        with patch("app.letterboxd.router.get_conn", make_get_conn(conn)):
            resp = TestClient(app).get("/api/letterboxd/profile")
        assert resp.status_code == 200
        assert resp.json() is None

    def test_returns_parsed_dict_when_data_is_json_string(self):
        stored = json.dumps({"username": "cinephile", "diary_count": 5})
        conn = FakeConn(fetchrow_results=[{"letterboxd_data": stored}])
        app = _make_app()
        with patch("app.letterboxd.router.get_conn", make_get_conn(conn)):
            resp = TestClient(app).get("/api/letterboxd/profile")
        assert resp.status_code == 200
        body = resp.json()
        assert body["username"] == "cinephile"
        assert body["diary_count"] == 5

    def test_returns_dict_passthrough_when_already_dict(self):
        stored = {"username": "cinephile", "avg_rating": 4.62}
        conn = FakeConn(fetchrow_results=[{"letterboxd_data": stored}])
        app = _make_app()
        with patch("app.letterboxd.router.get_conn", make_get_conn(conn)):
            resp = TestClient(app).get("/api/letterboxd/profile")
        assert resp.status_code == 200
        assert resp.json()["avg_rating"] == 4.62


# ── /letterboxd/analyze endpoint ──────────────────────────────────────────────


class TestLetterboxdAnalyzeEndpoint:
    def test_404_when_no_vibe_vectors_row(self):
        conn = FakeConn(fetchrow_results=[None])
        app = _make_app()
        with patch("app.letterboxd.router.get_conn", make_get_conn(conn)):
            resp = TestClient(app).get("/api/letterboxd/analyze")
        assert resp.status_code == 404

    def test_404_when_letterboxd_data_is_null(self):
        conn = FakeConn(fetchrow_results=[{"letterboxd_data": None}])
        app = _make_app()
        with patch("app.letterboxd.router.get_conn", make_get_conn(conn)):
            resp = TestClient(app).get("/api/letterboxd/analyze")
        assert resp.status_code == 404

    def test_200_with_narrative_when_data_present(self):
        stored = json.dumps({
            "username": "cinephile",
            "diary_count": 5,
            "recent_films": ["Stalker", "Solaris"],
            "avg_rating": 4.62,
            "watchlist_sample": ["Andrei Rublev"],
            "ratings_given": 4,
        })
        conn = FakeConn(fetchrow_results=[{"letterboxd_data": stored}])
        app = _make_app()
        with (
            patch("app.letterboxd.router.get_conn", make_get_conn(conn)),
            patch(
                "app.letterboxd.router.chat_completion",
                new=AsyncMock(return_value="You seek out the long, slow ache of Tarkovsky."),
            ),
        ):
            resp = TestClient(app).get("/api/letterboxd/analyze")
        assert resp.status_code == 200
        assert resp.json()["narrative"] == "You seek out the long, slow ache of Tarkovsky."


# ── /letterboxd/connect 503 guard ─────────────────────────────────────────────


class TestLetterboxdConnectEndpoint:
    def test_503_when_letterboxd_api_key_not_configured(self):
        """Missing LETTERBOXD_API_KEY → 503 before any state or DB call."""
        app = _make_app()
        with patch("app.letterboxd.router.get_settings") as mock_settings:
            mock_settings.return_value.letterboxd_api_key = None
            resp = TestClient(app).get("/api/letterboxd/connect")
        assert resp.status_code == 503
        assert "not configured" in resp.json()["detail"].lower()


# ── /letterboxd/ingest flow ───────────────────────────────────────────────────


class TestLetterboxdIngestEndpoint:
    def test_happy_path_distills_and_stores_profile(self):
        """Search → entries → watchlist all 200 → profile distilled and persisted."""
        search_data = {
            "items": [
                {
                    "type": "MemberSearchItem",
                    "member": {"username": "cinephile", "id": "member-1"},
                }
            ]
        }
        factory, client = _make_async_client([
            _mock_resp(200, search_data),
            _mock_resp(200, {"items": SAMPLE_ENTRIES}),
            _mock_resp(200, {"items": SAMPLE_WATCHLIST}),
        ])
        conn = FakeConn()
        store_mock = AsyncMock()
        app = _make_app()
        with (
            patch("app.letterboxd.router.httpx.AsyncClient", factory),
            patch("app.letterboxd.router._verify_state", new=AsyncMock(return_value=str(USER_ID))),
            patch("app.letterboxd.router.get_conn", make_get_conn(conn)),
            patch("app.letterboxd.router.store_provider_data", new=store_mock),
            patch("app.letterboxd.router.get_settings") as mock_settings,
        ):
            mock_settings.return_value.letterboxd_api_key = "key"
            mock_settings.return_value.letterboxd_api_secret = "secret"
            resp = TestClient(app).post(
                "/api/letterboxd/ingest",
                params={"username": "cinephile", "state": "dummy-state"},
            )
        assert resp.status_code == 200
        assert resp.json() == {"status": "connected", "username": "cinephile"}
        # store_provider_data called with the distilled profile under the right key
        store_mock.assert_called_once_with(str(USER_ID), "letterboxd_data", ANY)
        stored_profile = store_mock.call_args.args[2]
        assert stored_profile["username"] == "cinephile"
        assert stored_profile["diary_count"] == len(SAMPLE_ENTRIES)
        assert stored_profile["ratings_given"] == 4
        # users table username update executed
        assert any("letterboxd_username" in call[0] for call in conn.execute_calls)

    def test_404_when_username_not_found_in_search(self):
        """Search returns no matching member → 404, no store, only the search call made."""
        factory, client = _make_async_client([
            _mock_resp(200, {"items": []}),
        ])
        store_mock = AsyncMock()
        app = _make_app()
        with (
            patch("app.letterboxd.router.httpx.AsyncClient", factory),
            patch("app.letterboxd.router._verify_state", new=AsyncMock(return_value=str(USER_ID))),
            patch("app.letterboxd.router.store_provider_data", new=store_mock),
            patch("app.letterboxd.router.get_settings") as mock_settings,
        ):
            mock_settings.return_value.letterboxd_api_key = "key"
            mock_settings.return_value.letterboxd_api_secret = "secret"
            resp = TestClient(app).post(
                "/api/letterboxd/ingest",
                params={"username": "nobody", "state": "dummy-state"},
            )
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()
        store_mock.assert_not_called()
        assert client.get.call_count == 1
