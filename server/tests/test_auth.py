"""
Tests for server/app/auth/router.py — register, login, me, connectors.

Uses the FakeConn pattern from conftest.py (same as portrait tests).
Argon2 and JWT ops are mocked for speed — these tests verify HTTP behavior,
not cryptographic correctness.

Run:  cd server && python -m pytest tests/test_auth.py -v
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.auth.deps import get_current_user_id
from app.auth.router import router as auth_router
from tests.conftest import FakeConn, make_get_conn

_USER_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_TOKEN = "test.jwt.token"
_HASH = "$argon2id$v=19$m=19456,t=2,p=1$fakesalt$fakehash"


def _user_row(**overrides) -> dict:
    base = {
        "id": _USER_ID,
        "email": "user@example.com",
        "display_name": "Test User",
        "created_at": datetime.now(timezone.utc),
        "is_admin": False,
    }
    return {**base, **overrides}


def _make_app() -> FastAPI:
    app = FastAPI()
    app.include_router(auth_router)
    app.dependency_overrides[get_current_user_id] = lambda: _USER_ID
    return app


_client = TestClient(_make_app())


class TestRegister:
    def test_success_returns_201_with_token(self):
        conn = FakeConn(
            fetchval_results=[None],               # email not taken
            fetchrow_results=[{"id": _USER_ID}],   # INSERT RETURNING id
        )
        with patch("app.auth.router.get_conn", make_get_conn(conn)):
            with patch("app.auth.router.hash_password", return_value=_HASH):
                with patch("app.auth.router.create_access_token", return_value=_TOKEN):
                    r = _client.post("/register", json={
                        "email": "new@example.com",
                        "password": "pass1234",
                        "display_name": "New User",
                    })
        assert r.status_code == 201
        assert r.json()["access_token"] == _TOKEN

    def test_duplicate_email_returns_409(self):
        conn = FakeConn(fetchval_results=[str(_USER_ID)])  # email already taken
        with patch("app.auth.router.get_conn", make_get_conn(conn)):
            with patch("app.auth.router.hash_password", return_value=_HASH):
                r = _client.post("/register", json={
                    "email": "taken@example.com",
                    "password": "pass1234",
                    "display_name": "Dupe",
                })
        assert r.status_code == 409


class TestLogin:
    def test_valid_credentials_return_token(self):
        conn = FakeConn(fetchrow_results=[{"id": _USER_ID, "password_hash": _HASH}])
        with patch("app.auth.router.get_conn", make_get_conn(conn)):
            with patch("app.auth.router.verify_password", return_value=True):
                with patch("app.auth.router.create_access_token", return_value=_TOKEN):
                    r = _client.post("/login", json={
                        "email": "user@example.com",
                        "password": "correctpassword",
                    })
        assert r.status_code == 200
        assert r.json()["access_token"] == _TOKEN

    def test_unknown_email_returns_401(self):
        conn = FakeConn(fetchrow_results=[None])  # no user found
        with patch("app.auth.router.get_conn", make_get_conn(conn)):
            r = _client.post("/login", json={
                "email": "ghost@example.com",
                "password": "anything",
            })
        assert r.status_code == 401

    def test_wrong_password_returns_401(self):
        conn = FakeConn(fetchrow_results=[{"id": _USER_ID, "password_hash": _HASH}])
        with patch("app.auth.router.get_conn", make_get_conn(conn)):
            with patch("app.auth.router.verify_password", return_value=False):
                r = _client.post("/login", json={
                    "email": "user@example.com",
                    "password": "wrongpassword",
                })
        assert r.status_code == 401

    def test_error_detail_identical_for_unknown_email_and_wrong_password(self):
        """Both cases must return the same detail string to prevent email enumeration."""
        conn_no_user = FakeConn(fetchrow_results=[None])
        conn_wrong_pw = FakeConn(fetchrow_results=[{"id": _USER_ID, "password_hash": _HASH}])

        with patch("app.auth.router.get_conn", make_get_conn(conn_no_user)):
            r1 = _client.post("/login", json={"email": "ghost@example.com", "password": "x"})

        with patch("app.auth.router.get_conn", make_get_conn(conn_wrong_pw)):
            with patch("app.auth.router.verify_password", return_value=False):
                r2 = _client.post("/login", json={"email": "user@example.com", "password": "x"})

        assert r1.status_code == 401
        assert r2.status_code == 401
        assert r1.json()["detail"] == r2.json()["detail"]


class TestMe:
    def test_returns_current_user(self):
        conn = FakeConn(fetchrow_results=[_user_row()])
        with patch("app.auth.router.get_conn", make_get_conn(conn)):
            r = _client.get("/me")
        assert r.status_code == 200
        assert r.json()["email"] == "user@example.com"
        assert r.json()["is_admin"] is False

    def test_deleted_user_returns_404(self):
        conn = FakeConn(fetchrow_results=[None])
        with patch("app.auth.router.get_conn", make_get_conn(conn)):
            r = _client.get("/me")
        assert r.status_code == 404


class TestConnectors:
    def test_returns_connected_provider_list(self):
        conn = FakeConn(
            fetch_results=[[{"provider": "spotify"}, {"provider": "github"}]]
        )
        with patch("app.auth.router.get_conn", make_get_conn(conn)):
            r = _client.get("/connectors")
        assert r.status_code == 200
        assert sorted(r.json()) == ["github", "spotify"]

    def test_returns_empty_list_when_no_providers_connected(self):
        conn = FakeConn(fetch_results=[[]])
        with patch("app.auth.router.get_conn", make_get_conn(conn)):
            r = _client.get("/connectors")
        assert r.status_code == 200
        assert r.json() == []
