"""
Cross-connector correlations — finds meaningful patterns across provider data.
"""

from __future__ import annotations

import json
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..auth.deps import get_current_user_id
from ..config import get_settings
from ..db import get_conn

router = APIRouter()

# All *_data columns in vibe_vectors
_DATA_COLUMNS = [
    "spotify_data",
    "twitter_data",
    "strava_data",
    "gcal_data",
    "github_data",
    "youtube_data",
    "reddit_data",
    "letterboxd_data",
    "instagram_data",
    "tiktok_data",
    "costar_data",
]

# Map column name -> provider label
_COL_TO_PROVIDER = {col: col.replace("_data", "") for col in _DATA_COLUMNS}


@router.get("/correlations")
async def get_correlations(
    provider: str = Query(..., description="Provider to find correlations for"),
    user_id: UUID = Depends(get_current_user_id),
):
    """Find cross-connector correlations between the given provider and all others."""
    settings = get_settings()

    if not settings.openai_embed_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM not configured",
        )

    # Validate provider name
    target_col = f"{provider}_data"
    if target_col not in _DATA_COLUMNS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown provider: {provider}",
        )

    # Fetch all data columns
    cols = ", ".join(_DATA_COLUMNS)
    async with get_conn() as conn:
        row = await conn.fetchrow(
            f"SELECT {cols} FROM vibe_vectors WHERE user_id = $1",
            user_id,
        )

    if not row:
        return []

    # Parse each column into a dict (or None)
    provider_data: dict[str, dict] = {}
    for col in _DATA_COLUMNS:
        raw = row[col]
        if raw is not None:
            parsed = json.loads(raw) if isinstance(raw, str) else raw
            provider_data[_COL_TO_PROVIDER[col]] = parsed

    # Check the requested provider has data
    if provider not in provider_data:
        return []

    # Need at least 2 providers with data (including the requested one)
    if len(provider_data) < 2:
        return []

    # Build LLM request
    correlations = await _find_correlations(
        api_key=settings.openai_embed_key,
        target_provider=provider,
        all_data=provider_data,
    )
    return correlations


async def _find_correlations(
    api_key: str,
    target_provider: str,
    all_data: dict[str, dict],
) -> list[dict]:
    """Call the LLM to find cross-connector correlations."""

    other_providers = {k: v for k, v in all_data.items() if k != target_provider}

    prompt = f"""You are a data analyst finding meaningful correlations between a user's connected platform data.

TARGET PROVIDER: {target_provider}
TARGET DATA:
{json.dumps(all_data[target_provider], indent=2, default=str)}

OTHER CONNECTED PROVIDERS:
{json.dumps(other_providers, indent=2, default=str)}

Find 3-5 specific, meaningful correlations between {target_provider} and the other providers.
Each correlation should reference a specific field/metric from {target_provider} and a specific field/metric from another provider.

Return ONLY a valid JSON array with this exact schema (no markdown, no explanation):
[
  {{
    "source": {{ "provider": "{target_provider}", "field": "field.path", "value": <actual_value>, "label": "Human Label" }},
    "target": {{ "provider": "<other_provider>", "field": "field.path", "value": <actual_value>, "label": "Human Label" }},
    "explanation": "One sentence explaining the correlation"
  }}
]

Rules:
- Use actual values from the data above
- field paths should use dot notation for nested fields
- value should be the actual number, string, or boolean from the data
- Each correlation must involve {target_provider} as the source
- Return ONLY the JSON array, nothing else"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "gpt-4o-mini",
        "max_tokens": 1200,
        "messages": [{"role": "user", "content": prompt}],
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            json=payload,
            headers=headers,
        )
        if resp.status_code != 200:
            return []

        content = resp.json()["choices"][0]["message"]["content"]

    # Parse the LLM response as JSON
    try:
        # Strip markdown fences if the LLM wraps them
        text = content.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
        return json.loads(text)
    except (json.JSONDecodeError, KeyError, IndexError):
        return []
