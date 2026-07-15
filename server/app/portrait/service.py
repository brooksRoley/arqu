"""
Integrated Portrait service — gather, generate, persist.

Runs on the server LLM key only (llm.chat.chat_completion, env-driven
openai/openrouter). No BYOK: this instance is producer-provided free
software; narratives are a gift of the house, not metered to user keys.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from uuid import UUID

from ..db import get_conn
from ..llm.chat import chat_completion
from .models import Portrait
from .stitcher import (
    PROVIDER_COLUMNS,
    build_portrait_prompt,
    connected_providers,
    parse_portrait_json,
)

logger = logging.getLogger(__name__)

_PSYCH_FIELDS = (
    "ipip_neo_scores",
    "ecr_r_scores",
    "love_language",
    "sociosexual_orientation",
    "values_cluster",
)


class PortraitData:
    """Everything the router needs about a user's portrait state, in one fetch."""

    def __init__(
        self,
        profiles: dict[str, dict],
        psychometrics: dict,
        portrait: Portrait | None,
        generated_at: datetime | None,
        source_providers: list[str],
    ):
        self.profiles = profiles
        self.psychometrics = psychometrics
        self.portrait = portrait
        self.generated_at = generated_at
        self.source_providers = source_providers

    @property
    def connected(self) -> list[str]:
        return list(self.profiles.keys())


def _parse_stored_portrait(val) -> Portrait | None:
    if not val:
        return None
    try:
        payload = json.loads(val) if isinstance(val, str) else dict(val)
        return Portrait.model_validate(payload)
    except Exception:
        logger.warning("Stored portrait failed validation — treating as absent")
        return None


async def fetch_portrait_data(user_id: UUID) -> PortraitData:
    provider_cols = ", ".join(PROVIDER_COLUMNS.values())
    async with get_conn() as conn:
        row = await conn.fetchrow(
            f"""
            SELECT {provider_cols},
                   portrait, portrait_generated_at, portrait_source_providers
            FROM vibe_vectors
            WHERE user_id = $1
            """,
            user_id,
        )
        psych_row = await conn.fetchrow(
            f"SELECT {', '.join(_PSYCH_FIELDS)} FROM user_psychometrics WHERE user_id = $1",
            user_id,
        )

    if not row:
        return PortraitData({}, {}, None, None, [])

    psychometrics: dict = {}
    if psych_row:
        for key in _PSYCH_FIELDS:
            val = psych_row[key]
            if val is not None:
                psychometrics[key] = json.loads(val) if isinstance(val, str) else val

    return PortraitData(
        profiles=connected_providers(row),
        psychometrics=psychometrics,
        portrait=_parse_stored_portrait(row["portrait"]),
        generated_at=row["portrait_generated_at"],
        source_providers=list(row["portrait_source_providers"] or []),
    )


async def generate_and_store(user_id: UUID, data: PortraitData) -> Portrait:
    """Build the prompt, call the LLM (one parse retry), persist, return.

    Raises HTTPException 502/503 from chat_completion, ValueError if the
    output is unparseable after the retry.
    """
    prompt = build_portrait_prompt(data.profiles, data.psychometrics)

    raw = await chat_completion(prompt, max_tokens=2500, timeout=90.0)
    try:
        portrait = parse_portrait_json(raw, data.connected)
    except ValueError:
        logger.warning("Portrait parse failed for %s — retrying with strict suffix", user_id)
        raw = await chat_completion(
            prompt + "\n\nREMINDER: Output ONLY the raw JSON object. No prose, no markdown fences.",
            max_tokens=2500,
            timeout=90.0,
        )
        portrait = parse_portrait_json(raw, data.connected)

    async with get_conn() as conn:
        await conn.execute(
            """
            UPDATE vibe_vectors
            SET portrait = $1::jsonb,
                portrait_generated_at = now(),
                portrait_source_providers = $2,
                updated_at = now()
            WHERE user_id = $3
            """,
            json.dumps(portrait.model_dump()),
            data.connected,
            user_id,
        )
    logger.info("Portrait persisted for %s (%d providers)", user_id, len(data.connected))
    return portrait
