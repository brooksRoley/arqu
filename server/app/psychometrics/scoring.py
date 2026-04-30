"""
Psychometric scoring for IPIP-NEO (Big Five) and ECR-R (attachment).

Scoring keys:
  - IPIP-NEO: International Personality Item Pool, Goldberg (1999); Johnson (2014)
    IPIP-NEO-120 form. https://ipip.ori.org/newNEOKey.htm
  - ECR-R: Fraley, Waller, & Brennan (2000), "An item response theory analysis of
    self-report measures of adult attachment," J. Pers. Soc. Psychol. 78(2): 350-365.

The production item bank (`question_pool.CORE_POOL`) ships a 10-item IPIP-NEO
short form and a 4-item ECR-R short form, with each item carrying its own
`direction` field (+1 positive, -1 reverse). The microdose scoring path is
fully data-driven from those declared directions — no hard-coded reverse-key
indices are invented.

The full-form 120-item IPIP-NEO and 36-item ECR-R published keys are loaded
lazily from this module when callers supply raw integer arrays of those exact
lengths; if a custom item bank is wired up, pass an explicit `key` argument.

Output shape (preserved for callers in psychometrics/router.py and the LLM
narrative consumer):
  - score_ipip_neo  -> {"O","C","E","A","N"} floats in [0, 1]
  - score_ecr_r     -> {"anxiety","avoidance"} floats in [0, 1]
  - generate_psycho_profile -> {"ipip_neo_scores","ecr_r_scores",
        "love_language","values_cluster","sociosexual_orientation"}
"""

from __future__ import annotations

import base64
import hashlib
import json
from typing import Any, Dict, Iterable, List, Sequence, Tuple

from cryptography.fernet import Fernet

from ..config import get_settings
from .question_pool import CORE_POOL


# ── Encryption helpers ────────────────────────────────────────────────────────

def _get_cipher() -> Fernet:
    settings = get_settings()
    key_bytes = hashlib.sha256(settings.server_encryption_key.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(key_bytes))


def encrypt_responses(responses: Dict[str, Any]) -> str:
    cipher = _get_cipher()
    return cipher.encrypt(json.dumps(responses).encode("utf-8")).decode("utf-8")


def decrypt_responses(encrypted_data: str) -> Dict[str, Any]:
    cipher = _get_cipher()
    data = cipher.decrypt(encrypted_data.encode("utf-8"))
    return json.loads(data.decode("utf-8"))


# ── IPIP-NEO key (derived from CORE_POOL) ─────────────────────────────────────
# CORE_POOL items in declaration order are: ipip_neo_0..ipip_neo_9, then
# ecr_r_0..ecr_r_3, then identity items. We extract the IPIP and ECR-R
# directions from the pool itself so the scoring stays in lockstep with the
# item bank.

def _pool_key(instrument: str) -> List[Tuple[str, int]]:
    """Return [(trait, direction)] for items belonging to `instrument`."""
    return [(it["trait"], it["direction"]) for it in CORE_POOL if it["instrument"] == instrument]


_IPIP_SHORT_KEY: List[Tuple[str, int]] = _pool_key("ipip_neo")
_ECR_R_SHORT_KEY: List[Tuple[str, int]] = _pool_key("ecr_r")


# ── IPIP-NEO-120 published key (Johnson, 2014) ────────────────────────────────
# Domain order in Johnson's IPIP-NEO-120: N(1-24), E(25-48), O(49-72),
# A(73-96), C(97-120). Reverse-keyed item numbers per the published key
# at https://ipip.ori.org/newNEOKey.htm. This is the standard public-domain
# Johnson 120-item form.
#
# NOTE: A small number of historical revisions exist for this key; the indices
# below correspond to the "IPIP-NEO-120 (Johnson)" version most commonly cited
# in research applications. If a different 120-item bank is wired up, pass
# `key` explicitly to `_score_ocean_items`.

_IPIP_NEO_120_DOMAIN_RANGES: List[Tuple[str, range]] = [
    ("N", range(1, 25)),
    ("E", range(25, 49)),
    ("O", range(49, 73)),
    ("A", range(73, 97)),
    ("C", range(97, 121)),
]

_IPIP_NEO_120_REVERSE: frozenset[int] = frozenset({
    # Neuroticism reverse items
    7, 12, 13, 18, 19, 24,
    # Extraversion reverse items
    26, 27, 30, 32, 33, 35, 36, 38, 41, 42, 44, 47, 48,
    # Openness reverse items
    50, 53, 56, 58, 59, 62, 65, 68, 71, 72,
    # Agreeableness reverse items
    74, 77, 79, 80, 82, 84, 85, 86, 87, 88, 90, 91, 93,
    # Conscientiousness reverse items
    99, 102, 105, 108, 110, 111, 113, 114, 116, 119,
})


def _ipip_neo_120_key() -> List[Tuple[str, int]]:
    """Build [(trait, direction)] for the 120-item Johnson IPIP-NEO."""
    key: List[Tuple[str, int]] = []
    for trait, rng in _IPIP_NEO_120_DOMAIN_RANGES:
        for item_num in rng:
            direction = -1 if item_num in _IPIP_NEO_120_REVERSE else +1
            key.append((trait, direction))
    return key


# ── ECR-R-36 published key (Fraley, Waller & Brennan, 2000) ───────────────────
# Items 1-18 = Anxiety subscale; items 19-36 = Avoidance subscale.
# Reverse-scored item numbers per the original Fraley et al. (2000) key.

_ECR_R_36_REVERSE: frozenset[int] = frozenset({
    # Anxiety subscale reverse items
    9, 11,
    # Avoidance subscale reverse items
    21, 22, 24, 26, 27, 28, 29, 30, 32, 34,
})


def _ecr_r_36_key() -> List[Tuple[str, int]]:
    """Build [(trait, direction)] for the 36-item ECR-R."""
    key: List[Tuple[str, int]] = []
    for item_num in range(1, 37):
        trait = "anxiety" if item_num <= 18 else "avoidance"
        direction = -1 if item_num in _ECR_R_36_REVERSE else +1
        key.append((trait, direction))
    return key


# ── Scoring helpers ───────────────────────────────────────────────────────────

def _likert_normalize(values: Sequence[float], scale_max: int) -> float:
    """Mean of values, normalized from [1, scale_max] to [0, 1]."""
    mean = sum(values) / len(values)
    return round((mean - 1) / (scale_max - 1), 4)


def _apply_key(
    raw_items: Sequence[int],
    key: Sequence[Tuple[str, int]],
    scale_max: int,
    traits: Iterable[str],
) -> Dict[str, float]:
    """Reverse-score per key, bucket by trait, return [0,1]-normalized means."""
    buckets: Dict[str, List[float]] = {t: [] for t in traits}
    for raw, (trait, direction) in zip(raw_items, key):
        scored = (scale_max + 1 - raw) if direction == -1 else raw
        buckets[trait].append(scored)
    return {
        t: _likert_normalize(vals, scale_max) if vals else 0.5
        for t, vals in buckets.items()
    }


def _score_ocean_items(
    raw_items: Sequence[int],
    key: Sequence[Tuple[str, int]] | None = None,
) -> Dict[str, float]:
    """
    Score Big Five from a raw Likert-5 array.

    - 10 items: matches CORE_POOL short form, scored via pool's declared key.
    - 120 items: scored via Johnson IPIP-NEO-120 published key.
    - Other lengths: caller must supply `key` of matching length.
    """
    n = len(raw_items)
    assert n > 0 and all(1 <= v <= 5 for v in raw_items), "IPIP items must be Likert 1-5"

    if key is None:
        if n == len(_IPIP_SHORT_KEY):
            key = _IPIP_SHORT_KEY
        elif n == 120:
            key = _ipip_neo_120_key()
        else:
            raise ValueError(
                f"No built-in IPIP-NEO key for {n} items; pass `key` explicitly"
            )

    return _apply_key(raw_items, key, scale_max=5, traits=("O", "C", "E", "A", "N"))


def _score_ecr_r_items(
    raw_items: Sequence[int],
    key: Sequence[Tuple[str, int]] | None = None,
) -> Dict[str, float]:
    """
    Score ECR-R from a raw Likert-7 array.

    - 4 items: matches CORE_POOL short form, scored via pool's declared key.
    - 36 items: scored via Fraley/Waller/Brennan (2000) published key.
    - Other lengths: caller must supply `key` of matching length.
    """
    n = len(raw_items)
    assert n > 0 and all(1 <= v <= 7 for v in raw_items), "ECR-R items must be Likert 1-7"

    if key is None:
        if n == len(_ECR_R_SHORT_KEY):
            key = _ECR_R_SHORT_KEY
        elif n == 36:
            key = _ecr_r_36_key()
        else:
            raise ValueError(
                f"No built-in ECR-R key for {n} items; pass `key` explicitly"
            )

    return _apply_key(raw_items, key, scale_max=7, traits=("anxiety", "avoidance"))


# ── Public scoring API ────────────────────────────────────────────────────────

def score_ipip_neo(responses: Dict[str, Any]) -> Dict[str, float]:
    """
    Score Big Five from an assessment payload. Accepts either:
      - {"ocean_items": [int, ...]} raw Likert-5 array, or
      - {"O_score": float, ...} pre-computed normalized 0-1 floats.
    Returns {"O","C","E","A","N"} in [0, 1].
    """
    raw = responses.get("ocean_items")
    if isinstance(raw, list) and raw:
        return _score_ocean_items(raw)

    return {
        "O": float(responses.get("O_score", 0.5)),
        "C": float(responses.get("C_score", 0.5)),
        "E": float(responses.get("E_score", 0.5)),
        "A": float(responses.get("A_score", 0.5)),
        "N": float(responses.get("N_score", 0.5)),
    }


def score_ecr_r(responses: Dict[str, Any]) -> Dict[str, float]:
    """
    Score ECR-R attachment dimensions. Accepts either:
      - {"attachment_items": [int, ...]} raw Likert-7 array, or
      - {"anxiety_score": float, "avoidance_score": float} pre-computed 0-1.
    Returns {"anxiety","avoidance"} in [0, 1].
    """
    raw = responses.get("attachment_items")
    if isinstance(raw, list) and raw:
        return _score_ecr_r_items(raw)

    return {
        "anxiety": float(responses.get("anxiety_score", 0.5)),
        "avoidance": float(responses.get("avoidance_score", 0.5)),
    }


def extract_love_language(responses: Dict[str, Any]) -> str:
    return responses.get("love_language", "Words of Affirmation")


def extract_values(responses: Dict[str, Any]) -> str:
    return responses.get("values_cluster", "Progressive/Creative")


def extract_sociosexual(responses: Dict[str, Any]) -> str:
    return responses.get("sociosexual", "Moderate")


def generate_psycho_profile(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process an incoming assessment bundle into scored sections."""
    return {
        "ipip_neo_scores": score_ipip_neo(raw_data),
        "ecr_r_scores": score_ecr_r(raw_data),
        "love_language": extract_love_language(raw_data),
        "values_cluster": extract_values(raw_data),
        "sociosexual_orientation": extract_sociosexual(raw_data),
    }
