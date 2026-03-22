"""
Pinecone vector service — semantic memory layer for journal entries.

Journal text is embedded with llama-text-embed-v2 (via Pinecone inference)
and stored per-user. The intake confessional queries this index to surface
resonant memories before analysis.
"""

from __future__ import annotations

import asyncio
import logging
from functools import lru_cache

from pinecone import Pinecone, ServerlessSpec

from ..config import get_settings

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "llama-text-embed-v2"
EMBEDDING_DIMS = 1024
NAMESPACE = "journal"

# Module-level index cache (keyed by index name)
_index_cache: dict = {}


@lru_cache()
def _get_client() -> Pinecone | None:
    key = get_settings().pinecone_api_key
    if not key:
        return None
    return Pinecone(api_key=key)


def _get_index_sync():
    pc = _get_client()
    if pc is None:
        return None
    name = get_settings().pinecone_index
    if name not in _index_cache:
        existing = [i.name for i in pc.list_indexes()]
        if name not in existing:
            pc.create_index(
                name=name,
                dimension=EMBEDDING_DIMS,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )
        _index_cache[name] = pc.Index(name)
    return _index_cache[name]


def _embed_sync(texts: list[str], input_type: str) -> list[list[float]]:
    pc = _get_client()
    if pc is None:
        return []
    result = pc.inference.embed(
        model=EMBEDDING_MODEL,
        inputs=texts,
        parameters={"input_type": input_type, "truncate": "END"},
    )
    return [r.values for r in result]


async def embed_and_upsert(
    entry_id: str,
    user_id: str,
    text: str,
    text_preview: str,
    mood: str | None,
    created_at: str,
) -> None:
    """Fire-and-forget: embed a journal entry and upsert to Pinecone."""
    if not text.strip():
        return
    try:
        vectors = await asyncio.to_thread(_embed_sync, [text], "passage")
        if not vectors:
            return
        index = await asyncio.to_thread(_get_index_sync)
        if index is None:
            return
        metadata: dict = {
            "user_id": user_id,
            "text_preview": text_preview,
            "created_at": created_at,
        }
        if mood:
            metadata["mood"] = mood
        index.upsert(
            vectors=[{"id": entry_id, "values": vectors[0], "metadata": metadata}],
            namespace=NAMESPACE,
        )
    except Exception:
        logger.exception("Pinecone upsert failed for entry %s", entry_id)


async def query_relevant(user_id: str, query_text: str, top_k: int = 5) -> list[dict]:
    """Return metadata of top-K journal entries semantically closest to query_text."""
    try:
        vectors = await asyncio.to_thread(_embed_sync, [query_text], "query")
        if not vectors:
            return []
        index = await asyncio.to_thread(_get_index_sync)
        if index is None:
            return []
        results = index.query(
            vector=vectors[0],
            top_k=top_k,
            filter={"user_id": {"$eq": user_id}},
            include_metadata=True,
            namespace=NAMESPACE,
        )
        # Only return matches above similarity threshold
        return [m.metadata for m in results.matches if m.score > 0.5]
    except Exception:
        logger.exception("Pinecone query failed for user %s", user_id)
        return []
