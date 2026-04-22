"""Brain image library routes — upload, browse, traverse."""

from __future__ import annotations

import imghdr
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from .models import ImageRecord, TraverseBranch, TraverseResponse, UploadResponse
from .service import describe_image, embed_and_upsert_image, find_similar_images
from ..auth.deps import get_current_user_id
from ..db import get_conn, get_tx

router = APIRouter()

_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
_ALLOWED_TYPES = {"png", "jpeg", "gif", "webp", "bmp"}


def _mime_from_ext(filename: str | None) -> str:
    if not filename:
        return "image/png"
    ext = filename.rsplit(".", 1)[-1].lower()
    mapping = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
               "gif": "image/gif", "webp": "image/webp", "bmp": "image/bmp"}
    return mapping.get(ext, "image/png")


@router.post("/upload", response_model=UploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    user_id: UUID = Depends(get_current_user_id),
):
    """Upload an image → GPT-4o describe → embed → Pinecone + DB."""
    # Read and validate
    image_bytes = await file.read()
    if len(image_bytes) > _MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail="Image exceeds 10 MB limit")

    mime_type = _mime_from_ext(file.filename)
    pinecone_id = str(uuid4())

    # 1. Describe with GPT-4o vision
    description = await describe_image(image_bytes, mime_type)

    # 2. For MVP, store image as base64 data URL (swap to Vercel Blob later)
    import base64
    blob_url = f"data:{mime_type};base64,{base64.b64encode(image_bytes).decode()}"

    # 3. Embed description and upsert to Pinecone
    embedded = False
    if description:
        embedded = await embed_and_upsert_image(
            pinecone_id=pinecone_id,
            user_id=str(user_id),
            description=description,
            blob_url=f"/api/brain/image/{pinecone_id}",  # serve from DB, not inline data URL
            filename=file.filename,
        )

    # 4. Store in DB
    async with get_tx() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO brain_images (user_id, blob_url, filename, description, pinecone_id)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, blob_url, filename, description, width, height, created_at
            """,
            user_id, blob_url, file.filename, description, pinecone_id,
        )

    return UploadResponse(
        image=ImageRecord(**dict(row)),
        embedded=embedded,
    )


@router.get("/library")
async def list_images(
    user_id: UUID = Depends(get_current_user_id),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List the current user's brain images, newest first."""
    async with get_conn() as conn:
        rows = await conn.fetch(
            """
            SELECT id, blob_url, filename, description, width, height, created_at, pinecone_id
            FROM brain_images
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
            """,
            user_id, limit, offset,
        )
    return [dict(r) for r in rows]


@router.get("/traverse", response_model=TraverseResponse)
async def traverse(
    image_id: UUID = Query(..., description="DB id of the current image"),
    exclude: str = Query("", description="Comma-separated DB image IDs to exclude"),
    user_id: UUID = Depends(get_current_user_id),
):
    """Get the 3 most visually similar images to the given image."""
    # Resolve DB image → pinecone_id
    async with get_conn() as conn:
        row = await conn.fetchrow(
            "SELECT pinecone_id FROM brain_images WHERE id = $1 AND user_id = $2",
            image_id, user_id,
        )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")

    exclude_pinecone_ids: list[str] = []
    if exclude:
        db_ids = [e.strip() for e in exclude.split(",") if e.strip()]
        if db_ids:
            async with get_conn() as conn:
                excl_rows = await conn.fetch(
                    "SELECT pinecone_id FROM brain_images WHERE id = ANY($1::uuid[]) AND user_id = $2",
                    [UUID(i) for i in db_ids], user_id,
                )
                exclude_pinecone_ids = [r["pinecone_id"] for r in excl_rows]

    similar = await find_similar_images(
        image_pinecone_id=row["pinecone_id"],
        user_id=str(user_id),
        exclude_ids=exclude_pinecone_ids,
    )

    # Map pinecone_ids back to DB records
    if not similar:
        return TraverseResponse(branches=[])

    p_ids = [s["pinecone_id"] for s in similar]
    async with get_conn() as conn:
        db_rows = await conn.fetch(
            "SELECT id, blob_url, filename, pinecone_id FROM brain_images WHERE pinecone_id = ANY($1) AND user_id = $2",
            p_ids, user_id,
        )
    db_map = {r["pinecone_id"]: r for r in db_rows}

    branches = []
    for s in similar:
        db_rec = db_map.get(s["pinecone_id"])
        if not db_rec:
            continue
        branches.append(TraverseBranch(
            id=db_rec["id"],
            blob_url=db_rec["blob_url"],
            filename=db_rec["filename"],
            similarity=s["similarity"],
        ))

    return TraverseResponse(branches=branches)


@router.delete("/{image_id}")
async def delete_image(
    image_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
):
    """Remove an image from DB and Pinecone."""
    import asyncio
    from ..vector.service import _get_index_sync
    from .service import NAMESPACE_IMAGES

    async with get_tx() as conn:
        row = await conn.fetchrow(
            "DELETE FROM brain_images WHERE id = $1 AND user_id = $2 RETURNING pinecone_id",
            image_id, user_id,
        )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")

    # Clean up Pinecone vector
    try:
        index = await asyncio.to_thread(_get_index_sync)
        if index:
            await asyncio.to_thread(index.delete, ids=[row["pinecone_id"]], namespace=NAMESPACE_IMAGES)
    except Exception:
        pass  # DB is source of truth; Pinecone cleanup is best-effort

    return {"deleted": True}
