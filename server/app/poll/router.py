"""Poll token persistence routes."""

from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from .models import PollTokenCreate, PollTokenResponse
from ..auth.deps import get_current_user_id
from ..db import get_conn

router = APIRouter()


@router.post("/tokens", response_model=PollTokenResponse, status_code=status.HTTP_201_CREATED)
async def save_poll_token(
    body: PollTokenCreate,
    user_id: UUID = Depends(get_current_user_id),
):
    async with get_conn() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO poll_tokens (user_id, answers, theme, palette, tone, archetype, keywords)
            VALUES ($1, $2::jsonb, $3, $4::jsonb, $5, $6, $7)
            RETURNING id, user_id, answers, theme, palette, tone, archetype, keywords, created_at
            """,
            user_id,
            json.dumps(body.answers),
            body.theme,
            json.dumps(body.palette),
            body.tone,
            body.archetype,
            body.keywords,
        )
    return _row_to_response(row)


@router.get("/tokens/latest", response_model=PollTokenResponse)
async def get_latest_token(user_id: UUID = Depends(get_current_user_id)):
    async with get_conn() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, user_id, answers, theme, palette, tone, archetype, keywords, created_at
            FROM poll_tokens
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT 1
            """,
            user_id,
        )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No poll token found")
    return _row_to_response(row)


def _row_to_response(row) -> PollTokenResponse:
    d = dict(row)
    if isinstance(d.get("answers"), str):
        d["answers"] = json.loads(d["answers"])
    if isinstance(d.get("palette"), str):
        d["palette"] = json.loads(d["palette"])
    return PollTokenResponse(**d)
