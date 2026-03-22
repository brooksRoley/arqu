"""
Pinecone vector service — dual-namespace psychological mapping layer.

Namespace "users":
  One vector per user (ID = user UUID). Generated from intake confession text
  via OpenAI text-embedding-3-small (1,536 dims). Used for ANN matching
  ("find the 3 people closest to this user in psychological space") and karma
  penalties (Gaussian perturbation pushes toxic users into the margins).

Namespace "journal":
  One vector per journal entry. Used for semantic RAG during intake — surfaces
  resonant past entries as context before analysis.

Both namespaces share one Pinecone index at 1,536 dims (cosine).
"""

from __future__ import annotations

import asyncio
import logging

import httpx
import numpy as np
from pinecone import Pinecone, ServerlessSpec

from ..config import get_settings

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMS = 1536
NAMESPACE_USERS = "users"
NAMESPACE_JOURNAL = "journal"

_index_cache: dict = {}


def _get_client() -> Pinecone | None:
    key = get_settings().pinecone_api_key
    if not key:
        return None
    # Not cached with lru_cache — settings may not be available at import time
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


# ── Embedding ────────────────────────────────────────────────────────────────

async def _embed(text: str) -> list[float]:
    """Call OpenAI text-embedding-3-small. Returns [] if key not configured."""
    key = get_settings().openai_embed_key
    if not key:
        return []
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            "https://api.openai.com/v1/embeddings",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": EMBEDDING_MODEL, "input": text},
        )
        resp.raise_for_status()
    return resp.json()["data"][0]["embedding"]


# ── User vibe vectors ────────────────────────────────────────────────────────

async def upsert_user_vector(
    user_id: str,
    confession_text: str,
    attachment_style: str,
    defense_mechanism: str,
    readiness_score: int,
) -> bool:
    """
    Generate a 1,536-dim embedding from the user's confession text and
    store it as their psychological coordinate in Pinecone.
    Returns True on success.
    """
    try:
        vector = await _embed(confession_text)
        if not vector:
            return False
        index = await asyncio.to_thread(_get_index_sync)
        if index is None:
            return False
        await asyncio.to_thread(
            index.upsert,
            vectors=[{
                "id": user_id,
                "values": vector,
                "metadata": {
                    "user_id": user_id,
                    "attachment_style": attachment_style,
                    "defense_mechanism": defense_mechanism,
                    "readiness_score": readiness_score,
                },
            }],
            namespace=NAMESPACE_USERS,
        )
        return True
    except Exception:
        logger.exception("Pinecone user vector upsert failed for %s", user_id)
        return False


async def find_nearest_users(user_id: str, top_k: int = 3) -> list[dict]:
    """
    ANN lookup: return the top_k users psychologically closest to user_id.
    Excludes the querying user. Returns [] if user has no vector yet.
    """
    try:
        index = await asyncio.to_thread(_get_index_sync)
        if index is None:
            return []

        # Fetch the user's own vector to query against
        fetch_result = await asyncio.to_thread(
            index.fetch, ids=[user_id], namespace=NAMESPACE_USERS,
        )
        if user_id not in fetch_result.vectors:
            return []

        user_vector = fetch_result.vectors[user_id].values

        # top_k + 1 because the user will match themselves at score ~1.0
        query_result = await asyncio.to_thread(
            index.query,
            vector=user_vector,
            top_k=top_k + 1,
            include_metadata=True,
            namespace=NAMESPACE_USERS,
        )

        matches = [m for m in query_result.matches if m.id != user_id][:top_k]
        return [{"user_id": m.id, "score": round(m.score, 4), **m.metadata} for m in matches]
    except Exception:
        logger.exception("Pinecone ANN query failed for user %s", user_id)
        return []


async def apply_karma_penalty(user_id: str, karma_delta: float) -> None:
    """
    When a user's karma drops, add scaled Gaussian noise to their vector —
    pushing their coordinate point away from healthy clusters into the margins.
    karma_delta should be negative (e.g. -10 for a 10-point drop).
    """
    if karma_delta >= 0:
        return

    # Scale noise: a 100-point drop → σ=0.5 perturbation; clamp at 0.5
    penalty_scale = min(0.5, abs(karma_delta) / 100.0)

    try:
        index = await asyncio.to_thread(_get_index_sync)
        if index is None:
            return

        fetch_result = await asyncio.to_thread(
            index.fetch, ids=[user_id], namespace=NAMESPACE_USERS,
        )
        if user_id not in fetch_result.vectors:
            return

        record = fetch_result.vectors[user_id]
        arr = np.array(record.values, dtype=np.float32)
        noise = np.random.randn(len(arr)).astype(np.float32) * penalty_scale
        perturbed = arr + noise
        norm = np.linalg.norm(perturbed)
        penalized = (perturbed / norm).tolist() if norm > 0 else perturbed.tolist()

        await asyncio.to_thread(
            index.upsert,
            vectors=[{"id": user_id, "values": penalized, "metadata": record.metadata}],
            namespace=NAMESPACE_USERS,
        )
        logger.info("Karma penalty applied to %s (scale=%.3f)", user_id, penalty_scale)
    except Exception:
        logger.exception("Karma penalty failed for user %s", user_id)


# ── Journal RAG ──────────────────────────────────────────────────────────────

async def embed_and_upsert_journal(
    entry_id: str,
    user_id: str,
    text: str,
    text_preview: str,
    mood: str | None,
    created_at: str,
) -> None:
    """Fire-and-forget: embed a journal entry and store in the journal namespace."""
    if not text.strip():
        return
    try:
        vector = await _embed(text)
        if not vector:
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
        await asyncio.to_thread(
            index.upsert,
            vectors=[{"id": entry_id, "values": vector, "metadata": metadata}],
            namespace=NAMESPACE_JOURNAL,
        )
    except Exception:
        logger.exception("Pinecone journal upsert failed for entry %s", entry_id)


async def query_relevant_journal(user_id: str, query_text: str, top_k: int = 5) -> list[dict]:
    """Return metadata of top-K journal entries semantically closest to query_text."""
    try:
        vector = await _embed(query_text)
        if not vector:
            return []
        index = await asyncio.to_thread(_get_index_sync)
        if index is None:
            return []
        results = await asyncio.to_thread(
            index.query,
            vector=vector,
            top_k=top_k,
            filter={"user_id": {"$eq": user_id}},
            include_metadata=True,
            namespace=NAMESPACE_JOURNAL,
        )
        return [m.metadata for m in results.matches if m.score > 0.5]
    except Exception:
        logger.exception("Pinecone journal query failed for user %s", user_id)
        return []
