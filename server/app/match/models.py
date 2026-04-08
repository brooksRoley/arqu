"""Match interaction request/response models."""

from __future__ import annotations

from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class MatchAction(str, Enum):
    accept = "accept"
    reject = "reject"


class InteractRequest(BaseModel):
    target_id: UUID
    action: MatchAction


class InteractResponse(BaseModel):
    recorded: bool
    mutual_match: bool
    target_id: str
    action: str
