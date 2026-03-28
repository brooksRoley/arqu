from __future__ import annotations

import json
from uuid import UUID
from typing import Dict, Any, Optional

from fastapi import HTTPException, status
import httpx

from ..db import get_pool
from .encryption import decrypt_api_key

async def generate_psychoanalysis_narrative(user_id: UUID, profile_data: Dict[str, Any]) -> str:
    """
    Generates a subjective, warm, and insightful psychological narrative 
    based on the user's computed psychometric scores and behavioral data.
    """
    pool = get_pool()
    
    # Try Anthropic first, then OpenAI as fallback
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT provider, encrypted_key, key_nonce 
            FROM user_api_keys 
            WHERE user_id = $1 AND provider IN ('anthropic', 'openai')
            ORDER BY provider = 'anthropic' DESC
            LIMIT 1
            """,
            user_id
        )
        # Also let's try to get spotify behavioral data from vibe_vectors
        vibe_row = await conn.fetchrow(
            "SELECT spotify_data FROM vibe_vectors WHERE user_id = $1", 
            user_id
        )
        
    if not row:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="To generate a psychoanalysis narrative, please connect an Anthropic or OpenAI API key."
        )
        
    api_key = decrypt_api_key(row["encrypted_key"], row["key_nonce"])
    provider = row["provider"]
    
    spotify_data = None
    if vibe_row and vibe_row["spotify_data"]:
        try:
            spotify_data = json.loads(vibe_row["spotify_data"])
        except json.JSONDecodeError:
            pass

    prompt = _build_prompt(profile_data, spotify_data)
    
    if provider == "anthropic":
        return await _call_anthropic(api_key, prompt)
    else:
        return await _call_openai(api_key, prompt)

def _build_prompt(profile: Dict[str, Any], spotify_data: Optional[Dict[str, Any]]) -> str:
    spotify_context = ""
    if spotify_data:
        artists = ", ".join(spotify_data.get("top_artists", []))
        genres = ", ".join(spotify_data.get("genres", []))
        spotify_context = f"\n- Behavioral Audio Preferences (Spotify): Top Genres include {genres}. This often correlates with openness and extraversion levels."
        
    return f"""
You are an expert, warm, and highly insightful relationship psychologist.
Based on the following psychometric assessment data, write a personalized 3-paragraph 
psychoanalysis that helps the user understand their relationship patterns. 
Do not use cold clinical jargon. Be empowering and accurate to the data.

DATA:
- Big Five (IPIP-NEO-50): {json.dumps(profile.get('ipip_neo_scores'))}
- Attachment Style (ECR-R): {json.dumps(profile.get('ecr_r_scores'))}
- Love Language: {profile.get('love_language')}
- Values Cluster: {profile.get('values_cluster')}
- Sociosexual Orientation: {profile.get('sociosexual_orientation')}{spotify_context}

Focus mainly on how their attachment style and Big Five traits interact in dating. Cross-reference their behavioral data (e.g. Spotify) to look for potential public/private self discrepancies if any exist. Keep the tone warm, insightful, and constructive. Return only the narrative content.
"""

async def _call_anthropic(api_key: str, prompt: str) -> str:
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": "claude-3-5-sonnet-20240620",
        "max_tokens": 1024,
        "messages": [
            {"role": "user", "content": prompt}
        ],
    }
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers)
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail="Upstream LLM error")
        data = resp.json()
        return data["content"][0]["text"]

async def _call_openai(api_key: str, prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "gpt-4o",
        "max_tokens": 1024,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail="Upstream LLM error")
        data = resp.json()
        return data["choices"][0]["message"]["content"]
