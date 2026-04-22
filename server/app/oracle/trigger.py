"""Auto-trigger Oracle synthesis when a user connects enough providers."""

from __future__ import annotations

import asyncio
import json
import logging
from uuid import UUID

from ..db import get_conn
from .models import SynthesisRequest, ProviderPayload
from .service import synthesize_and_upsert

logger = logging.getLogger(__name__)

_PROVIDER_COLUMNS = {
    "spotify": "spotify_data",
    "twitter": "twitter_data",
    "strava": "strava_data",
    # Future: "gcal": "gcal_data", "costar": "costar_data", etc.
}

_MIN_PROVIDERS = 2  # Minimum connected providers to trigger synthesis


async def maybe_trigger_synthesis(user_id: UUID) -> None:
    """
    Check if the user has enough connected providers to trigger Oracle synthesis.
    If so, build a SynthesisRequest from real DB data and fire it as a background task.
    """
    async with get_conn() as conn:
        row = await conn.fetchrow(
            """
            SELECT spotify_data, twitter_data, strava_data,
                   gcal_data, costar_data, letterboxd_data, steam_data
            FROM vibe_vectors
            WHERE user_id = $1
            """,
            user_id,
        )

    if not row:
        return

    # Count non-null, non-empty provider data
    connected = 0
    for col in _PROVIDER_COLUMNS.values():
        val = row[col]
        if val and val != {} and val != "{}":
            connected += 1

    if connected < _MIN_PROVIDERS:
        logger.debug("User %s has %d providers — need %d for synthesis", user_id, connected, _MIN_PROVIDERS)
        return

    # Build SynthesisRequest from real data
    def _parse(val) -> dict:
        if not val:
            return {}
        if isinstance(val, str):
            return json.loads(val)
        return dict(val)

    request = SynthesisRequest(
        spotify=ProviderPayload(data=_parse(row["spotify_data"])),
        twitter=ProviderPayload(data=_parse(row["twitter_data"])),
        strava=ProviderPayload(data=_parse(row["strava_data"])),
        gcal=ProviderPayload(data=_parse(row["gcal_data"])),
        costar=ProviderPayload(data=_parse(row["costar_data"])),
        letterboxd=ProviderPayload(data=_parse(row["letterboxd_data"])),
        steam=ProviderPayload(data=_parse(row["steam_data"])),
    )

    logger.info("Auto-triggering Oracle synthesis for %s (%d providers)", user_id, connected)
    asyncio.create_task(synthesize_and_upsert(str(user_id), request))
