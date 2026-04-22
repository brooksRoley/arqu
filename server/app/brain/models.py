"""Brain image library — request/response models."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ImageRecord(BaseModel):
    id: UUID
    blob_url: str
    filename: str | None
    description: str | None
    width: int | None
    height: int | None
    created_at: datetime


class UploadResponse(BaseModel):
    image: ImageRecord
    embedded: bool


class TraverseBranch(BaseModel):
    id: UUID
    blob_url: str
    filename: str | None
    similarity: float


class TraverseResponse(BaseModel):
    branches: list[TraverseBranch]
