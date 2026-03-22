"""Poll token models."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class PollTokenCreate(BaseModel):
    answers: dict
    theme: str
    palette: dict
    tone: str | None = None
    archetype: str | None = None
    keywords: list[str] = []


class PollTokenResponse(BaseModel):
    id: UUID
    user_id: UUID | None
    answers: dict
    theme: str
    palette: dict
    tone: str | None
    archetype: str | None
    keywords: list[str]
    created_at: datetime
