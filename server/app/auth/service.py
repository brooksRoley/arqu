"""Auth business logic — password hashing, JWT creation/verification."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

import argon2
import jwt

from ..config import get_settings

_hasher = argon2.PasswordHasher(
    time_cost=2,
    memory_cost=19456,
    parallelism=1,
)


def hash_password(plain: str) -> str:
    return _hasher.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _hasher.verify(hashed, plain)
    except argon2.exceptions.VerifyMismatchError:
        return False
    except argon2.exceptions.InvalidHashError:
        return False


def create_access_token(user_id: UUID) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict | None:
    """Decode and verify a JWT. Returns payload dict or None if invalid/expired."""
    settings = get_settings()
    try:
        return jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None
