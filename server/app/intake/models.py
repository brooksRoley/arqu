"""Intake confessional request/response models."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, field_validator


_MAX_CONFESSIONS = 20
_MAX_CONFESSION_LENGTH = 5_000  # chars per confession


class ConfessRequest(BaseModel):
    confessions: list[str]
    journal_context: str | None = None
    poll_theme: str | None = None

    @field_validator("confessions")
    @classmethod
    def validate_confessions(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("At least one confession is required")
        if len(v) > _MAX_CONFESSIONS:
            raise ValueError(f"Maximum {_MAX_CONFESSIONS} confessions allowed")
        for i, confession in enumerate(v):
            if len(confession) > _MAX_CONFESSION_LENGTH:
                raise ValueError(
                    f"Confession {i + 1} exceeds {_MAX_CONFESSION_LENGTH} character limit"
                )
        return v


class ConfessResponse(BaseModel):
    attachment_style: str
    defense_mechanism: str
    readiness_score: int
    insight: str
    memories: list[str] = []  # resonant journal snippets surfaced by Pinecone


class FittingRequest(BaseModel):
    phase: Literal["self", "ideal"]
    data: dict


class VibeVectorResponse(BaseModel):
    id: UUID
    user_id: UUID
    attachment_style: str
    defense_mechanism: str
    readiness_score: int
    poll_theme: str | None
    created_at: datetime
