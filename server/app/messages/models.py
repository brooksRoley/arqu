from __future__ import annotations

from pydantic import BaseModel, field_validator
from uuid import UUID


class SendRequest(BaseModel):
    recipient_id: UUID
    body: str

    @field_validator("body")
    @classmethod
    def body_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Message body cannot be empty")
        if len(v) > 2000:
            raise ValueError("Message body exceeds 2000 characters")
        return v


class MessageOut(BaseModel):
    id: str
    sender_id: str
    recipient_id: str
    body: str
    read_at: str | None
    created_at: str


class ThreadSummary(BaseModel):
    other_user_id: str
    other_user_name: str
    last_message: str | None
    last_message_at: str | None
    unread_count: int
