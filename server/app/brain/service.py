"""
Brain image service — vision description → text embedding → Pinecone.

Pipeline per image:
1. GPT-4o vision describes the image (rich text description)
2. text-embedding-3-small embeds that description → 1,536-dim vector
3. Upsert to Pinecone "images" namespace with metadata
"""

from __future__ import annotations

import asyncio
import base64
import logging
from pathlib import Path
from uuid import uuid4

import httpx

from ..config import get_settings
from ..vector.service import _embed, _get_index_sync

logger = logging.getLogger(__name__)

NAMESPACE_IMAGES = "images"


async def describe_image(image_bytes: bytes, mime_type: str = "image/png") -> str:
    """Use GPT-4o vision to generate a rich description of an image."""
    key = get_settings().openai_embed_key
    if not key:
        return ""

    b64 = base64.b64encode(image_bytes).decode()
    data_url = f"data:{mime_type};base64,{b64}"

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "gpt-4o",
                "max_tokens": 300,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "Describe this image in detail for visual similarity matching. "
                                    "Include: dominant colors, composition, subjects, style, mood, "
                                    "textures, lighting, and any notable visual elements. "
                                    "Be specific and visual — this description will be used to "
                                    "find similar images."
                                ),
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": data_url, "detail": "low"},
                            },
                        ],
                    }
                ],
            },
        )
        resp.raise_for_status()

    return resp.json()["choices"][0]["message"]["content"]


async def embed_and_upsert_image(
    pinecone_id: str,
    user_id: str,
    description: str,
    blob_url: str,
    filename: str | None,
) -> bool:
    """Embed image description and upsert to Pinecone images namespace."""
    try:
        vector = await _embed(description)
        if not vector:
            return False
        index = await asyncio.to_thread(_get_index_sync)
        if index is None:
            return False
        await asyncio.to_thread(
            index.upsert,
            vectors=[{
                "id": pinecone_id,
                "values": vector,
                "metadata": {
                    "user_id": user_id,
                    "blob_url": blob_url,
                    "filename": filename or "",
                    "description_preview": description[:200],
                },
            }],
            namespace=NAMESPACE_IMAGES,
        )
        return True
    except Exception:
        logger.exception("Pinecone image upsert failed for %s", pinecone_id)
        return False


async def find_similar_images(
    image_pinecone_id: str,
    user_id: str,
    exclude_ids: list[str] | None = None,
    top_k: int = 3,
    min_score: float = 0.4,
) -> list[dict]:
    """Find visually similar images by querying the current image's vector."""
    try:
        index = await asyncio.to_thread(_get_index_sync)
        if index is None:
            return []

        fetch_result = await asyncio.to_thread(
            index.fetch, ids=[image_pinecone_id], namespace=NAMESPACE_IMAGES,
        )
        if image_pinecone_id not in fetch_result.vectors:
            return []

        vector = fetch_result.vectors[image_pinecone_id].values

        excludes = set(exclude_ids or [])
        excludes.add(image_pinecone_id)

        # Fetch extra to account for exclusions
        query_result = await asyncio.to_thread(
            index.query,
            vector=vector,
            top_k=top_k + len(excludes) + 1,
            filter={"user_id": {"$eq": user_id}},
            include_metadata=True,
            namespace=NAMESPACE_IMAGES,
        )

        branches = []
        for m in query_result.matches:
            if m.id in excludes:
                continue
            if m.score < min_score:
                continue
            branches.append({
                "pinecone_id": m.id,
                "similarity": round(m.score, 4),
                "blob_url": m.metadata.get("blob_url", ""),
                "filename": m.metadata.get("filename", ""),
            })
            if len(branches) >= top_k:
                break

        return branches
    except Exception:
        logger.exception("Pinecone image similarity query failed for %s", image_pinecone_id)
        return []
