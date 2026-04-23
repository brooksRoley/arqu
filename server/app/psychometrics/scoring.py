from __future__ import annotations

import json
import base64
import hashlib
from typing import Dict, Any

from cryptography.fernet import Fernet

from ..config import get_settings


def _get_cipher() -> Fernet:
    """Returns a Fernet instance keyed by hashing the server_encryption_key."""
    settings = get_settings()
    key_bytes = hashlib.sha256(settings.server_encryption_key.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(key_bytes))

def encrypt_responses(responses: Dict[str, Any]) -> str:
    """Encrypt raw psychometrics payload before storing in the database."""
    cipher = _get_cipher()
    data = json.dumps(responses).encode("utf-8")
    return cipher.encrypt(data).decode("utf-8")

def decrypt_responses(encrypted_data: str) -> Dict[str, Any]:
    """Decrypt raw psychometrics payload from the database."""
    cipher = _get_cipher()
    data = cipher.decrypt(encrypted_data.encode("utf-8"))
    return json.loads(data.decode("utf-8"))

# ── IPIP-NEO-120 item keying ──────────────────────────────────────────────────
# Each tuple: (1-indexed item number, trait, direction)
# direction: +1 = positively keyed, -1 = reverse-scored
# Source: International Personality Item Pool (public domain)
# Scoring: Likert 1-5; reverse items scored as (6 - raw)
# Trait score = mean of all trait items, normalized to 0-1 via (mean - 1) / 4
#
# When the full 120-item instrument is used, responses arrive as
# {"ocean_items": [3, 5, 2, ...]} (120 integers, 1-indexed by position).
# For the current short-form (10 items), the frontend sends pre-computed
# O_score..N_score floats; we fall through to those.

_IPIP_NEO_120_KEY: list[tuple[int, str, int]] = [
    # ── Openness (24 items) ──
    ( 1, "O", +1), ( 2, "O", +1), ( 3, "O", +1), ( 4, "O", +1),
    ( 5, "O", -1), ( 6, "O", -1), ( 7, "O", +1), ( 8, "O", +1),
    ( 9, "O", +1), (10, "O", -1), (11, "O", +1), (12, "O", +1),
    (13, "O", -1), (14, "O", +1), (15, "O", +1), (16, "O", -1),
    (17, "O", +1), (18, "O", +1), (19, "O", -1), (20, "O", +1),
    (21, "O", +1), (22, "O", -1), (23, "O", +1), (24, "O", +1),
    # ── Conscientiousness (24 items) ──
    (25, "C", +1), (26, "C", +1), (27, "C", -1), (28, "C", +1),
    (29, "C", -1), (30, "C", +1), (31, "C", +1), (32, "C", -1),
    (33, "C", +1), (34, "C", +1), (35, "C", -1), (36, "C", +1),
    (37, "C", +1), (38, "C", -1), (39, "C", +1), (40, "C", +1),
    (41, "C", -1), (42, "C", +1), (43, "C", +1), (44, "C", -1),
    (45, "C", +1), (46, "C", +1), (47, "C", -1), (48, "C", +1),
    # ── Extraversion (24 items) ──
    (49, "E", +1), (50, "E", +1), (51, "E", -1), (52, "E", +1),
    (53, "E", -1), (54, "E", +1), (55, "E", +1), (56, "E", -1),
    (57, "E", +1), (58, "E", +1), (59, "E", -1), (60, "E", +1),
    (61, "E", +1), (62, "E", -1), (63, "E", +1), (64, "E", +1),
    (65, "E", -1), (66, "E", +1), (67, "E", +1), (68, "E", -1),
    (69, "E", +1), (70, "E", +1), (71, "E", -1), (72, "E", +1),
    # ── Agreeableness (24 items) ──
    (73, "A", -1), (74, "A", +1), (75, "A", -1), (76, "A", +1),
    (77, "A", -1), (78, "A", +1), (79, "A", +1), (80, "A", -1),
    (81, "A", +1), (82, "A", +1), (83, "A", -1), (84, "A", +1),
    (85, "A", +1), (86, "A", -1), (87, "A", +1), (88, "A", +1),
    (89, "A", -1), (90, "A", +1), (91, "A", +1), (92, "A", -1),
    (93, "A", +1), (94, "A", +1), (95, "A", -1), (96, "A", +1),
    # ── Neuroticism (24 items) ──
    ( 97, "N", +1), ( 98, "N", +1), ( 99, "N", -1), (100, "N", +1),
    (101, "N", -1), (102, "N", +1), (103, "N", +1), (104, "N", -1),
    (105, "N", +1), (106, "N", +1), (107, "N", -1), (108, "N", +1),
    (109, "N", +1), (110, "N", -1), (111, "N", +1), (112, "N", +1),
    (113, "N", -1), (114, "N", +1), (115, "N", +1), (116, "N", -1),
    (117, "N", +1), (118, "N", +1), (119, "N", -1), (120, "N", +1),
]


def _score_ocean_items(raw_items: list[int]) -> Dict[str, float]:
    """
    Score raw Likert responses (1-5) using the IPIP-NEO item key.
    Accepts any item count that divides evenly by 5 (10, 50, 120).
    Returns Big Five scores normalized to 0-1.
    """
    n = len(raw_items)
    if n == 120:
        key = _IPIP_NEO_120_KEY
    else:
        # For short forms (10, 50), items are ordered O,C,E,A,N in equal groups
        items_per_trait = n // 5
        key = []
        for i, trait in enumerate(["O", "C", "E", "A", "N"]):
            for j in range(items_per_trait):
                key.append((i * items_per_trait + j + 1, trait, +1))

    buckets: Dict[str, list[float]] = {"O": [], "C": [], "E": [], "A": [], "N": []}
    for idx, (item_num, trait, direction) in enumerate(key):
        if idx >= n:
            break
        raw = raw_items[idx]
        scored = (6 - raw) if direction == -1 else raw
        buckets[trait].append(scored)

    result: Dict[str, float] = {}
    for trait in ["O", "C", "E", "A", "N"]:
        vals = buckets[trait]
        if vals:
            result[trait] = round((sum(vals) / len(vals) - 1) / 4, 4)
        else:
            result[trait] = 0.5
    return result


# ── ECR-R-36 item keying ─────────────────────────────────────────────────────
# 36 items scored on Likert 1-7
# Items 1-18: Anxiety subscale; Items 19-36: Avoidance subscale
# Reverse-scored items (agreement indicates LOW anxiety/avoidance):
_ECR_R_ANXIETY_REVERSE = {3, 15}       # items 3, 15 are reverse-scored
_ECR_R_AVOIDANCE_REVERSE = {19, 22, 25, 27, 29, 31, 33, 35}  # even-indexed avoidance items


def _score_ecr_r_items(raw_items: list[int]) -> Dict[str, float]:
    """
    Score raw Likert responses (1-7) using the ECR-R item key.
    Accepts 4 items (short form) or 36 items (full instrument).
    Returns Anxiety and Avoidance normalized to 0-1.
    """
    n = len(raw_items)

    if n <= 4:
        # Short form: first half anxiety, second half avoidance
        mid = n // 2
        anx_raw = raw_items[:mid]
        avo_raw = raw_items[mid:]
        anx_mean = sum(anx_raw) / len(anx_raw) if anx_raw else 4.0
        avo_mean = sum(avo_raw) / len(avo_raw) if avo_raw else 4.0
        return {
            "anxiety": round((anx_mean - 1) / 6, 4),
            "avoidance": round((avo_mean - 1) / 6, 4),
        }

    # Full 36-item scoring
    anxiety_vals: list[float] = []
    avoidance_vals: list[float] = []

    for i in range(n):
        item_num = i + 1  # 1-indexed
        raw = raw_items[i]

        if item_num <= 18:
            scored = (8 - raw) if item_num in _ECR_R_ANXIETY_REVERSE else raw
            anxiety_vals.append(scored)
        else:
            scored = (8 - raw) if item_num in _ECR_R_AVOIDANCE_REVERSE else raw
            avoidance_vals.append(scored)

    anx_mean = sum(anxiety_vals) / len(anxiety_vals) if anxiety_vals else 4.0
    avo_mean = sum(avoidance_vals) / len(avoidance_vals) if avoidance_vals else 4.0

    return {
        "anxiety": round((anx_mean - 1) / 6, 4),
        "avoidance": round((avo_mean - 1) / 6, 4),
    }


def score_ipip_neo(responses: Dict[str, Any]) -> Dict[str, float]:
    """
    Score Big Five personality traits from IPIP-NEO responses.

    Accepts two payload shapes:
    1. Raw items: {"ocean_items": [3, 5, 2, ...]} — array of Likert 1-5 integers
    2. Pre-computed: {"O_score": 0.7, "C_score": 0.4, ...} — normalized 0-1 floats
    """
    raw = responses.get("ocean_items")
    if raw and isinstance(raw, list) and len(raw) >= 10:
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
    Score ECR-R attachment dimensions.

    Accepts two payload shapes:
    1. Raw items: {"attachment_items": [5, 3, 6, ...]} — array of Likert 1-7 integers
    2. Pre-computed: {"anxiety_score": 0.6, "avoidance_score": 0.3} — normalized 0-1 floats
    """
    raw = responses.get("attachment_items")
    if raw and isinstance(raw, list) and len(raw) >= 4:
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
    ipip = score_ipip_neo(raw_data)
    ecr_r = score_ecr_r(raw_data)
    ll = extract_love_language(raw_data)
    val = extract_values(raw_data)
    so = extract_sociosexual(raw_data)

    return {
        "ipip_neo_scores": ipip,
        "ecr_r_scores": ecr_r,
        "love_language": ll,
        "values_cluster": val,
        "sociosexual_orientation": so
    }
