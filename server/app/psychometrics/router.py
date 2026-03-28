from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from ..auth.deps import get_current_user_id
from ..db import get_pool
from .scoring import generate_psycho_profile, encrypt_responses
from ..llm.psychoanalysis import generate_psychoanalysis_narrative

router = APIRouter()

class AssessmentPayload(BaseModel):
    responses: Dict[str, Any]

@router.post("/submit")
async def submit_assessment(payload: AssessmentPayload, user_id: UUID = Depends(get_current_user_id)):
    """Accept the multi-part assessment and store the scored results."""
    pool = get_pool()

    profile = generate_psycho_profile(payload.responses)
    encrypted_raw = encrypt_responses(payload.responses)

    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO user_psychometrics 
                (user_id, scorable_responses, ipip_neo_scores, ecr_r_scores, 
                 love_language, sociosexual_orientation, values_cluster, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, now())
            ON CONFLICT (user_id) DO UPDATE SET
                scorable_responses = EXCLUDED.scorable_responses,
                ipip_neo_scores = EXCLUDED.ipip_neo_scores,
                ecr_r_scores = EXCLUDED.ecr_r_scores,
                love_language = EXCLUDED.love_language,
                sociosexual_orientation = EXCLUDED.sociosexual_orientation,
                values_cluster = EXCLUDED.values_cluster,
                updated_at = now()
        """, 
        str(user_id), 
        encrypted_raw, 
        json.dumps(profile["ipip_neo_scores"]), 
        json.dumps(profile["ecr_r_scores"]), 
        profile["love_language"], 
        profile["sociosexual_orientation"], 
        profile["values_cluster"])
        
    return {"status": "success", "profile": profile}

@router.get("/profile")
async def get_my_profile(user_id: UUID = Depends(get_current_user_id)):
    """Fetch the user's computed psychometric profile."""
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT ipip_neo_scores, ecr_r_scores, love_language, sociosexual_orientation, values_cluster, narrative
            FROM user_psychometrics
            WHERE user_id = $1
        """, str(user_id))
    
    if not row:
        raise HTTPException(status_code=404, detail="No psychometric profile found.")

    return {
        "ipip_neo_scores": json.loads(row["ipip_neo_scores"]) if isinstance(row["ipip_neo_scores"], str) else row["ipip_neo_scores"],
        "ecr_r_scores": json.loads(row["ecr_r_scores"]) if isinstance(row["ecr_r_scores"], str) else row["ecr_r_scores"],
        "love_language": row["love_language"],
        "sociosexual_orientation": row["sociosexual_orientation"],
        "values_cluster": row["values_cluster"],
        "narrative": row["narrative"]
    }

@router.post("/narrative")
async def generate_narrative(user_id: UUID = Depends(get_current_user_id)):
    """Triggers the LLM psychoanalysis based on current scores."""
    pool = get_pool()
    
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT ipip_neo_scores, ecr_r_scores, love_language, sociosexual_orientation, values_cluster
            FROM user_psychometrics
            WHERE user_id = $1
        """, str(user_id))
        
    if not row:
        raise HTTPException(status_code=404, detail="No profile found to analyze. Please submit the assessment first.")
        
    profile_data = {
        "ipip_neo_scores": json.loads(row["ipip_neo_scores"]) if isinstance(row["ipip_neo_scores"], str) else row["ipip_neo_scores"],
        "ecr_r_scores": json.loads(row["ecr_r_scores"]) if isinstance(row["ecr_r_scores"], str) else row["ecr_r_scores"],
        "love_language": row["love_language"],
        "sociosexual_orientation": row["sociosexual_orientation"],
        "values_cluster": row["values_cluster"]
    }
    
    narrative = await generate_psychoanalysis_narrative(user_id, profile_data)
    
    async with pool.acquire() as conn:
        await conn.execute("UPDATE user_psychometrics SET narrative = $1 WHERE user_id = $2", narrative, str(user_id))
        
    return {"status": "success", "narrative": narrative}

@router.delete("/profile")
async def delete_my_profile(user_id: UUID = Depends(get_current_user_id)):
    """Allow users to delete their psychometric data for privacy."""
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM user_psychometrics WHERE user_id = $1", str(user_id))
    return {"status": "success", "message": "Psychometric data deleted."}
