"""Oracle synthesis — request/response models."""

from __future__ import annotations

import json

from pydantic import BaseModel, field_validator


_MAX_PROVIDER_PAYLOAD_BYTES = 50_000  # 50KB per provider


class ProviderPayload(BaseModel):
    """Raw ingested data from a single OAuth provider. Empty dict = not connected."""
    data: dict = {}

    @field_validator("data")
    @classmethod
    def limit_payload_size(cls, v: dict) -> dict:
        if len(json.dumps(v, default=str)) > _MAX_PROVIDER_PAYLOAD_BYTES:
            raise ValueError(
                f"Provider payload exceeds {_MAX_PROVIDER_PAYLOAD_BYTES // 1000}KB limit"
            )
        return v


class SynthesisRequest(BaseModel):
    """All seven provider payloads fed into the Oracle."""
    spotify: ProviderPayload = ProviderPayload()
    twitter: ProviderPayload = ProviderPayload()
    gcal: ProviderPayload = ProviderPayload()
    strava: ProviderPayload = ProviderPayload()
    costar: ProviderPayload = ProviderPayload()
    letterboxd: ProviderPayload = ProviderPayload()
    steam: ProviderPayload = ProviderPayload()


class PsychCoordinate(BaseModel):
    """The LLM-synthesized psychological coordinate."""
    empathy_index: float
    isolation_metric: float
    fatalism_score: float
    masochism_curve: float
    oracle_rationale: str
    suggested_community_action: str


class SynthesisResponse(BaseModel):
    status: str
    message: str
