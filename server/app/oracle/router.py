"""Oracle routes — trigger the 7-dimensional psychological synthesis pipeline."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends

from ..auth.deps import get_current_user_id
from .models import SynthesisRequest, SynthesisResponse
from .service import synthesize_and_upsert

router = APIRouter()


@router.post("/synthesize", response_model=SynthesisResponse)
async def trigger_synthesis(
    body: SynthesisRequest,
    background_tasks: BackgroundTasks,
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Accept raw data from all seven OAuth providers and kick off
    Oracle synthesis as a background task.  The LLM call + embedding +
    Pinecone upsert runs async so the frontend feels instant.
    """
    background_tasks.add_task(synthesize_and_upsert, str(user_id), body)
    return SynthesisResponse(
        status="initiated",
        message="The Oracle is plotting your coordinate.",
    )
