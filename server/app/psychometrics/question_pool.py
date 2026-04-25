"""
Psychometric question pool for the post-trance microdose system.

Each item has:
- item_id: unique identifier
- instrument: which psychometric instrument it belongs to
- text: the question text shown to the user
- scale: "likert_5", "likert_7", or "categorical"
- options: list of options for categorical items (None for Likert)
- connector_affinity: "spotify", "strava", or "general"
- trait: scoring key (e.g. "O" for openness, "anxiety" for ECR-R)
- direction: +1 for positively keyed, -1 for reverse-scored (Likert only)
"""

from __future__ import annotations

from typing import TypedDict


class PoolItem(TypedDict):
    item_id: str
    instrument: str
    text: str
    scale: str
    options: list[str] | None
    connector_affinity: str
    trait: str
    direction: int


# ── Core Pool (17 items) ─────────────────────────────────────────────────────

CORE_POOL: list[PoolItem] = [
    # IPIP-NEO Big Five (10 items, Likert 1-5)
    {
        "item_id": "ipip_neo_0", "instrument": "ipip_neo",
        "text": "I have a rich imagination and love exploring abstract ideas.",
        "scale": "likert_5", "options": None,
        "connector_affinity": "spotify", "trait": "O", "direction": 1,
    },
    {
        "item_id": "ipip_neo_1", "instrument": "ipip_neo",
        "text": "I am always prepared and like to plan things in advance.",
        "scale": "likert_5", "options": None,
        "connector_affinity": "strava", "trait": "C", "direction": 1,
    },
    {
        "item_id": "ipip_neo_2", "instrument": "ipip_neo",
        "text": "I love being around people and am the life of the party.",
        "scale": "likert_5", "options": None,
        "connector_affinity": "spotify", "trait": "E", "direction": 1,
    },
    {
        "item_id": "ipip_neo_3", "instrument": "ipip_neo",
        "text": "I feel empathy for others and make people feel at ease.",
        "scale": "likert_5", "options": None,
        "connector_affinity": "general", "trait": "A", "direction": 1,
    },
    {
        "item_id": "ipip_neo_4", "instrument": "ipip_neo",
        "text": "I am easily stressed and often feel anxious or unsettled.",
        "scale": "likert_5", "options": None,
        "connector_affinity": "general", "trait": "N", "direction": 1,
    },
    {
        "item_id": "ipip_neo_5", "instrument": "ipip_neo",
        "text": "I am quick to understand new concepts and enjoy intellectual challenges.",
        "scale": "likert_5", "options": None,
        "connector_affinity": "spotify", "trait": "O", "direction": 1,
    },
    {
        "item_id": "ipip_neo_6", "instrument": "ipip_neo",
        "text": "I pay attention to detail and follow through on commitments.",
        "scale": "likert_5", "options": None,
        "connector_affinity": "strava", "trait": "C", "direction": 1,
    },
    {
        "item_id": "ipip_neo_7", "instrument": "ipip_neo",
        "text": "I feel energized after spending time in social settings.",
        "scale": "likert_5", "options": None,
        "connector_affinity": "general", "trait": "E", "direction": 1,
    },
    {
        "item_id": "ipip_neo_8", "instrument": "ipip_neo",
        "text": "I try to understand others' perspectives before forming opinions.",
        "scale": "likert_5", "options": None,
        "connector_affinity": "general", "trait": "A", "direction": 1,
    },
    {
        "item_id": "ipip_neo_9", "instrument": "ipip_neo",
        "text": "My mood fluctuates frequently and I can be easily upset.",
        "scale": "likert_5", "options": None,
        "connector_affinity": "general", "trait": "N", "direction": 1,
    },
    # ECR-R Attachment (4 items, Likert 1-7)
    {
        "item_id": "ecr_r_0", "instrument": "ecr_r",
        "text": "I worry about being abandoned by the people I am close to.",
        "scale": "likert_7", "options": None,
        "connector_affinity": "general", "trait": "anxiety", "direction": 1,
    },
    {
        "item_id": "ecr_r_1", "instrument": "ecr_r",
        "text": "I need a lot of reassurance that I am loved.",
        "scale": "likert_7", "options": None,
        "connector_affinity": "general", "trait": "anxiety", "direction": 1,
    },
    {
        "item_id": "ecr_r_2", "instrument": "ecr_r",
        "text": "I prefer not to share my feelings or problems with partners.",
        "scale": "likert_7", "options": None,
        "connector_affinity": "strava", "trait": "avoidance", "direction": 1,
    },
    {
        "item_id": "ecr_r_3", "instrument": "ecr_r",
        "text": "I feel comfortable depending on others for emotional support.",
        "scale": "likert_7", "options": None,
        "connector_affinity": "general", "trait": "avoidance", "direction": -1,
    },
    # Identity (3 items, categorical)
    {
        "item_id": "identity_love_language", "instrument": "identity",
        "text": "What makes you feel most valued?",
        "scale": "categorical",
        "options": ["Words of Affirmation", "Quality Time", "Gifts", "Acts of Service", "Physical Touch"],
        "connector_affinity": "general", "trait": "love_language", "direction": 0,
    },
    {
        "item_id": "identity_values", "instrument": "identity",
        "text": "What drives you most?",
        "scale": "categorical",
        "options": ["Traditional", "Career-driven", "Creative", "Progressive", "Adventure", "Spiritual"],
        "connector_affinity": "strava", "trait": "values_cluster", "direction": 0,
    },
    {
        "item_id": "identity_sociosexual", "instrument": "identity",
        "text": "How do you approach intimacy?",
        "scale": "categorical",
        "options": ["Restricted", "Moderate", "Unrestricted"],
        "connector_affinity": "general", "trait": "sociosexual_orientation", "direction": 0,
    },
]


def get_pool() -> list[PoolItem]:
    """Return the full question pool (core for now, extended later)."""
    return CORE_POOL


def get_next_item(
    answered_ids: set[str],
    connector: str | None = None,
) -> PoolItem | None:
    """
    Return the next unanswered item, preferring items with matching connector_affinity.
    Falls back to 'general' affinity if no connector-specific items remain.
    Returns None when everything is answered.
    """
    pool = get_pool()
    unanswered = [item for item in pool if item["item_id"] not in answered_ids]
    if not unanswered:
        return None

    if connector:
        # Try connector-specific first
        matched = [item for item in unanswered if item["connector_affinity"] == connector]
        if matched:
            return matched[0]

    # Fall back to general or any remaining
    general = [item for item in unanswered if item["connector_affinity"] == "general"]
    if general:
        return general[0]

    return unanswered[0]
