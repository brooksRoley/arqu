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

def score_ipip_neo_50(responses: Dict[str, Any]) -> Dict[str, float]:
    """
    Given raw responses for IPIP-NEO-50, compute Big Five trait scores.
    Currently, this is a placeholder stub. In a full implementation, it groups the 50 items 
    into 5 facets and normalizes them.
    """
    return {
        "O": responses.get("O_score", 0.5),
        "C": responses.get("C_score", 0.5),
        "E": responses.get("E_score", 0.5),
        "A": responses.get("A_score", 0.5),
        "N": responses.get("N_score", 0.5)
    }

def score_ecr_r(responses: Dict[str, Any]) -> Dict[str, float]:
    """
    Score the Experiences in Close Relationships - Revised.
    Returns Anxiety and Avoidance dimensions based on the 36 items.
    """
    return {
        "anxiety": responses.get("anxiety_score", 0.5),
        "avoidance": responses.get("avoidance_score", 0.5)
    }

def extract_love_language(responses: Dict[str, Any]) -> str:
    return responses.get("love_language", "Words of Affirmation")

def extract_values(responses: Dict[str, Any]) -> str:
    return responses.get("values_cluster", "Progressive/Creative")

def extract_sociosexual(responses: Dict[str, Any]) -> str:
    return responses.get("sociosexual", "Moderate")

def generate_psycho_profile(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process an incoming assessment bundle into scored sections."""
    ipip = score_ipip_neo_50(raw_data)
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
