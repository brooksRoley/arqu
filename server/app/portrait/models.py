"""Pydantic models for the Integrated Portrait."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class PortraitSection(BaseModel):
    title: str
    body: str
    # Provider keys this section draws on — powers the frontend's
    # link-back chips to /calibrate/:provider. Validated against the
    # user's actually-connected set before persisting.
    providers: list[str] = []


class Portrait(BaseModel):
    headline: str
    sections: list[PortraitSection]
    throughline: str


PortraitState = Literal["ready", "stale", "empty", "insufficient_providers", "no_llm"]


class PortraitStatus(BaseModel):
    status: PortraitState
    portrait: Portrait | None = None
    generated_at: datetime | None = None
    source_providers: list[str] = []
    connected_providers: list[str] = []
    llm_available: bool = False
