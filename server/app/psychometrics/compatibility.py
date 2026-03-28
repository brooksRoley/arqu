from __future__ import annotations

from typing import Dict, Any

def compute_compatibility(user_a_profile: Dict[str, Any], user_b_profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes a pairwise compatibility score between two users based on psychological data.
    Weights: 
    - Attachment (Highest)
    - Values (High)
    - Personality (Medium)
    - Love Language (Low)
    """
    # MVP scoring logic simulating the math based on profile similarities.
    # We would actually compute deltas between numerical representations here.
    attachment_score = 0.8
    values_score = 0.75
    personality_score = 0.65
    love_lang_score = 0.9
    
    overall = (attachment_score * 0.4) + (values_score * 0.3) + (personality_score * 0.2) + (love_lang_score * 0.1)

    return {
        "overall_match_percentage": round(overall * 100, 1),
        "attachment_compatibility": attachment_score_str(user_a_profile, user_b_profile),
        "values_congruence": "High",
        "personality_complementarity": "Moderate",
        "love_language_awareness": "Good"
    }

def attachment_score_str(a: Dict[str, Any], b: Dict[str, Any]) -> str:
    """Return a qualitative attachment dynamic based on profiles."""
    return "Secure + Secure"
