"""Vector routes — zeromind session storage + vibe vector enrichment."""

from __future__ import annotations

import json
import logging
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..auth.deps import get_current_user_id
from ..db import get_conn

logger = logging.getLogger(__name__)

router = APIRouter()


class ZeromindSession(BaseModel):
    dominant_phase: str
    session_duration_ms: int
    sync_count: int = 0
    coherence_peak: float = 0.0
    modules_used: list[str] = []


@router.post("/zeromind", status_code=204)
async def store_zeromind_session(
    body: ZeromindSession,
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Store a completed trance/entrainment session and fold the data
    into the user's vibe vector metadata for richer matching.
    """
    session_data = {
        "dominant_phase": body.dominant_phase,
        "session_duration_ms": body.session_duration_ms,
        "sync_count": body.sync_count,
        "coherence_peak": body.coherence_peak,
        "modules_used": body.modules_used,
    }

    async with get_conn() as conn:
        # Store zeromind data alongside other provider data in vibe_vectors
        await conn.execute(
            """
            UPDATE vibe_vectors
            SET zeromind_data = $2::jsonb, updated_at = now()
            WHERE user_id = $1
            """,
            user_id, json.dumps(session_data),
        )

    logger.info("Zeromind session stored for %s (phase=%s, duration=%dms)",
                user_id, body.dominant_phase, body.session_duration_ms)
