"""
Pairwise psychometric compatibility.

Inputs are profile dicts as stored in `user_psychometrics` and returned by
`generate_psycho_profile`:
  - ipip_neo_scores: {"O","C","E","A","N"} norm-referenced floats in [0,1]
  - ecr_r_scores: {"anxiety","avoidance","attachment_style"}
  - values_cluster: str (one of the CORE_POOL identity_values options)
  - love_language: str (one of the CORE_POOL identity_love_language options)
  - sociosexual_orientation: str

Weighting follows the dating-research literature:
  attachment (0.40) > values (0.30) > personality (0.20) > love language (0.10)
"""

from __future__ import annotations

import math
from typing import Any, Dict, Tuple


# ── Attachment ────────────────────────────────────────────────────────────────
# Two-dimensional model (Bartholomew & Horowitz, 1991; Fraley et al., 2000).
# Higher compatibility when both partners are low on anxiety AND avoidance
# (secure-secure). The "anxious + avoidant" combination is the well-documented
# pursuit-withdrawal trap and is penalised explicitly.

def _attachment_score(a_ecr: Dict[str, Any], b_ecr: Dict[str, Any]) -> float:
    a_anx = float(a_ecr.get("anxiety", 0.5))
    a_avo = float(a_ecr.get("avoidance", 0.5))
    b_anx = float(b_ecr.get("anxiety", 0.5))
    b_avo = float(b_ecr.get("avoidance", 0.5))

    # Base: both partners' distance from secure quadrant (0,0).
    # Each user's insecurity = mean(anx, avo); pair insecurity = mean of both.
    pair_insecurity = (a_anx + a_avo + b_anx + b_avo) / 4.0
    base = 1.0 - pair_insecurity

    # Pursuit-withdrawal penalty: one partner high-anxiety, other high-avoidance.
    pw1 = max(0.0, a_anx - 0.5) * max(0.0, b_avo - 0.5)
    pw2 = max(0.0, b_anx - 0.5) * max(0.0, a_avo - 0.5)
    penalty = (pw1 + pw2) * 1.2  # up to ~0.3 at extreme corners

    return max(0.0, min(1.0, base - penalty))


def attachment_dynamic_label(
    a_ecr: Dict[str, Any], b_ecr: Dict[str, Any]
) -> str:
    a_style = a_ecr.get("attachment_style", "Secure")
    b_style = b_ecr.get("attachment_style", "Secure")
    # Canonical ordering so "Secure + Preoccupied" == "Preoccupied + Secure".
    pair = " + ".join(sorted([a_style, b_style]))
    return pair


# ── Personality (Big Five) ────────────────────────────────────────────────────
# Empirical research on partner similarity (Dyrenforth, Kashy, Donnellan &
# Lucas, 2010; Gonzaga, Carter & Buckwalter, 2010): assortative similarity
# matters most for A, C, N. E and O are weaker / more complementary signals.

_OCEAN_WEIGHTS: Dict[str, float] = {
    "A": 0.30,
    "C": 0.25,
    "N": 0.25,
    "E": 0.10,
    "O": 0.10,
}


def _personality_score(a_ipip: Dict[str, Any], b_ipip: Dict[str, Any]) -> float:
    total_w = 0.0
    weighted_sim = 0.0
    for trait, w in _OCEAN_WEIGHTS.items():
        a_v = float(a_ipip.get(trait, 0.5))
        b_v = float(b_ipip.get(trait, 0.5))
        # Similarity = 1 - |Δ|. Inputs already in [0,1] (norm percentile).
        sim = 1.0 - abs(a_v - b_v)
        weighted_sim += sim * w
        total_w += w
    return weighted_sim / total_w if total_w else 0.5


def _personality_label(score: float) -> str:
    if score >= 0.80:
        return "Strong"
    if score >= 0.60:
        return "Moderate"
    if score >= 0.40:
        return "Mixed"
    return "Low"


# ── Values ────────────────────────────────────────────────────────────────────
# CORE_POOL identity_values options:
#   Traditional, Career-driven, Creative, Progressive, Adventure, Spiritual
# Adjacency reflects which clusters tend to coexist or be compatible.

_VALUES_NEIGHBORS: Dict[str, set[str]] = {
    "Traditional":    {"Spiritual", "Career-driven"},
    "Career-driven":  {"Traditional", "Adventure"},
    "Creative":       {"Progressive", "Spiritual", "Adventure"},
    "Progressive":    {"Creative", "Adventure"},
    "Adventure":      {"Creative", "Progressive", "Career-driven"},
    "Spiritual":      {"Traditional", "Creative"},
}


def _values_score(a_val: str | None, b_val: str | None) -> Tuple[float, str]:
    if not a_val or not b_val:
        return 0.5, "Unknown"
    if a_val == b_val:
        return 1.0, "High"
    if b_val in _VALUES_NEIGHBORS.get(a_val, set()):
        return 0.7, "Moderate"
    return 0.35, "Divergent"


# ── Love language ─────────────────────────────────────────────────────────────
# Chapman's framework (Words of Affirmation, Quality Time, Gifts, Acts of
# Service, Physical Touch). Matching language correlates with perceived
# responsiveness; mismatched but adjacent languages are workable with awareness.

_LOVE_LANG_ADJACENT: Dict[str, set[str]] = {
    "Words of Affirmation": {"Quality Time"},
    "Quality Time":         {"Words of Affirmation", "Physical Touch"},
    "Gifts":                {"Acts of Service"},
    "Acts of Service":      {"Gifts", "Quality Time"},
    "Physical Touch":       {"Quality Time"},
}


def _love_language_score(a_ll: str | None, b_ll: str | None) -> Tuple[float, str]:
    if not a_ll or not b_ll:
        return 0.5, "Unknown"
    if a_ll == b_ll:
        return 1.0, "Aligned"
    if b_ll in _LOVE_LANG_ADJACENT.get(a_ll, set()):
        return 0.7, "Good"
    return 0.4, "Needs awareness"


# ── Public API ────────────────────────────────────────────────────────────────

_WEIGHTS = {
    "attachment":  0.40,
    "values":      0.30,
    "personality": 0.20,
    "love_lang":   0.10,
}


def compute_compatibility(
    user_a_profile: Dict[str, Any],
    user_b_profile: Dict[str, Any],
) -> Dict[str, Any]:
    """Compute pairwise compatibility between two scored psychometric profiles."""
    a_ecr  = user_a_profile.get("ecr_r_scores")  or {}
    b_ecr  = user_b_profile.get("ecr_r_scores")  or {}
    a_ipip = user_a_profile.get("ipip_neo_scores") or {}
    b_ipip = user_b_profile.get("ipip_neo_scores") or {}

    attachment = _attachment_score(a_ecr, b_ecr)
    personality = _personality_score(a_ipip, b_ipip)
    values, values_label = _values_score(
        user_a_profile.get("values_cluster"),
        user_b_profile.get("values_cluster"),
    )
    love_lang, love_lang_label = _love_language_score(
        user_a_profile.get("love_language"),
        user_b_profile.get("love_language"),
    )

    overall = (
        attachment  * _WEIGHTS["attachment"]
        + values    * _WEIGHTS["values"]
        + personality * _WEIGHTS["personality"]
        + love_lang * _WEIGHTS["love_lang"]
    )

    return {
        "overall_match_percentage": round(overall * 100, 1),
        "attachment_compatibility": attachment_dynamic_label(a_ecr, b_ecr),
        "attachment_score": round(attachment, 4),
        "values_congruence": values_label,
        "values_score": round(values, 4),
        "personality_complementarity": _personality_label(personality),
        "personality_score": round(personality, 4),
        "love_language_awareness": love_lang_label,
        "love_language_score": round(love_lang, 4),
    }


def attachment_score_str(a: Dict[str, Any], b: Dict[str, Any]) -> str:
    """Back-compat shim: qualitative label for the attachment pair."""
    return attachment_dynamic_label(
        a.get("ecr_r_scores") or {},
        b.get("ecr_r_scores") or {},
    )
