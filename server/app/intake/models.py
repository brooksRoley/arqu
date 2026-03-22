"""Intake confessional request/response models."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ConfessRequest(BaseModel):
    confessions: list[str]
    journal_context: str | None = None
    poll_theme: str | None = None


class ConfessResponse(BaseModel):
    attachment_style: str
    defense_mechanism: str
    readiness_score: int
    insight: str
    memories: list[str] = []  # resonant journal snippets surfaced by Pinecone


class VibeVectorResponse(BaseModel):
    id: UUID
    user_id: UUID
    attachment_style: str
    defense_mechanism: str
    readiness_score: int
    poll_theme: str | None
    created_at: datetime
