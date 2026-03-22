"""Auth dependencies — injectable current-user extraction for FastAPI routes."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .service import decode_access_token
from ..db import get_conn

_bearer = HTTPBearer(auto_error=False)


async def get_current_user_id(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> UUID:
    """Extract and validate user_id from the Authorization: Bearer <token> header."""
    if creds is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(creds.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return UUID(payload["sub"])


async def get_optional_user_id(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> Optional[UUID]:
    """Like get_current_user_id but returns None for unauthenticated requests.
    Use this for endpoints that work for both guests and logged-in users."""
    if creds is None:
        return None
    payload = decode_access_token(creds.credentials)
    if payload is None:
        return None
    return UUID(payload["sub"])
