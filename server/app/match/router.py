"""Match interaction routes — accept/reject + mutual match detection."""

from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from ..auth.deps import get_current_user_id
from ..db import get_conn
from .models import InteractRequest, InteractResponse

router = APIRouter()


@router.post("/interact", response_model=InteractResponse)
async def interact(
    body: InteractRequest,
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Record an accept/reject decision for a matched user.
    If both users have accepted each other, returns mutual_match=True.
    Uses UPSERT so a user can change their mind (reject -> accept or vice versa).
    """
    if body.target_id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot interact with yourself",
        )

    async with get_conn() as conn:
        # Upsert the interaction
        await conn.execute(
            """
            INSERT INTO match_interactions (actor_id, target_id, action)
            VALUES ($1, $2, $3)
            ON CONFLICT (actor_id, target_id) DO UPDATE SET
                action = EXCLUDED.action,
                created_at = now()
            """,
            user_id, body.target_id, body.action.value,
        )

        # Check for mutual match (both accepted)
        mutual = False
        if body.action.value == "accept":
            row = await conn.fetchrow(
                """
                SELECT 1 FROM match_interactions
                WHERE actor_id = $1 AND target_id = $2 AND action = 'accept'
                """,
                body.target_id, user_id,
            )
            mutual = row is not None

        # If mutual match, record karma event for both users
        if mutual:
            for uid in (user_id, body.target_id):
                await conn.execute(
                    """
                    INSERT INTO karma_ledger (user_id, event_type, karma_delta, metadata)
                    VALUES ($1, 'POS_HANDSHAKE', 10, $2::jsonb)
                    """,
                    uid,
                    f'{{"matched_with": "{body.target_id if uid == user_id else str(user_id)}"}}',
                )

    return InteractResponse(
        recorded=True,
        mutual_match=mutual,
        target_id=str(body.target_id),
        action=body.action.value,
    )


@router.get("/new")
async def get_new_matches(user_id: UUID = Depends(get_current_user_id)):
    """Return mutual matches the user hasn't seen yet."""
    async with get_conn() as conn:
        rows = await conn.fetch(
            """
            SELECT
                CASE WHEN a.actor_id = $1 THEN a.target_id ELSE a.actor_id END AS matched_user_id,
                GREATEST(a.created_at, b.created_at) AS matched_at
            FROM match_interactions a
            JOIN match_interactions b
                ON  a.actor_id  = b.target_id
                AND a.target_id = b.actor_id
            WHERE a.action = 'accept' AND b.action = 'accept'
              AND (a.actor_id = $1 OR a.target_id = $1)
              AND a.actor_id < a.target_id
              AND NOT EXISTS (
                  SELECT 1 FROM match_seen ms
                  WHERE ms.user_id = $1
                    AND ms.match_id = CASE WHEN a.actor_id = $1 THEN a.target_id ELSE a.actor_id END
              )
            """,
            user_id,
        )

        # Hydrate display names
        match_ids = [r["matched_user_id"] for r in rows]
        if match_ids:
            user_rows = await conn.fetch(
                "SELECT id, display_name, avatar_url FROM users WHERE id = ANY($1::uuid[])",
                match_ids,
            )
            user_map = {r["id"]: r for r in user_rows}
        else:
            user_map = {}

    return [
        {
            "user_id": str(r["matched_user_id"]),
            "display_name": user_map.get(r["matched_user_id"], {}).get("display_name") or "Someone",
            "avatar_url": user_map.get(r["matched_user_id"], {}).get("avatar_url"),
            "matched_at": r["matched_at"].isoformat(),
        }
        for r in rows
    ]


@router.post("/seen")
async def mark_matches_seen(user_id: UUID = Depends(get_current_user_id)):
    """Mark all current mutual matches as seen."""
    async with get_conn() as conn:
        await conn.execute(
            """
            INSERT INTO match_seen (user_id, match_id)
            SELECT $1,
                   CASE WHEN a.actor_id = $1 THEN a.target_id ELSE a.actor_id END
            FROM match_interactions a
            JOIN match_interactions b
                ON  a.actor_id  = b.target_id
                AND a.target_id = b.actor_id
            WHERE a.action = 'accept' AND b.action = 'accept'
              AND (a.actor_id = $1 OR a.target_id = $1)
              AND a.actor_id < a.target_id
            ON CONFLICT DO NOTHING
            """,
            user_id,
        )
    return {"acknowledged": True}


@router.get("/mutual")
async def get_mutual_matches(user_id: UUID = Depends(get_current_user_id)):
    """Return all mutual matches for the current user."""
    async with get_conn() as conn:
        rows = await conn.fetch(
            """
            SELECT
                CASE WHEN a.actor_id = $1 THEN a.target_id ELSE a.actor_id END AS matched_user_id,
                GREATEST(a.created_at, b.created_at) AS matched_at
            FROM match_interactions a
            JOIN match_interactions b
                ON  a.actor_id  = b.target_id
                AND a.target_id = b.actor_id
            WHERE a.action = 'accept' AND b.action = 'accept'
              AND (a.actor_id = $1 OR a.target_id = $1)
              AND a.actor_id < a.target_id
            """,
            user_id,
        )

    return [
        {"user_id": str(r["matched_user_id"]), "matched_at": r["matched_at"].isoformat()}
        for r in rows
    ]


@router.get("/reveal/{target_id}")
async def get_reveal(
    target_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
):
    """Return the full signal story for a mutual match pair."""
    async with get_conn() as conn:
        mutual = await conn.fetchrow(
            """
            SELECT 1 FROM match_interactions a
            JOIN match_interactions b
                ON a.actor_id = b.target_id AND a.target_id = b.actor_id
            WHERE a.action = 'accept' AND b.action = 'accept'
              AND a.actor_id = $1 AND a.target_id = $2
            """,
            user_id, target_id,
        )
        if not mutual:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No mutual match found with this user",
            )

        my_vibe = await conn.fetchrow(
            """
            SELECT user_id, spotify_data, twitter_data, strava_data, steam_data,
                   oracle_coordinate, attachment_style, defense_mechanism,
                   fitting_self, fitting_ideal,
                   (spotify_data IS NOT NULL) AS has_spotify,
                   (twitter_data IS NOT NULL) AS has_twitter,
                   (strava_data IS NOT NULL) AS has_strava,
                   (steam_data IS NOT NULL) AS has_steam,
                   (oracle_coordinate IS NOT NULL) AS has_oracle
            FROM vibe_vectors WHERE user_id = $1
            """,
            user_id,
        )
        their_vibe = await conn.fetchrow(
            """
            SELECT user_id, spotify_data, twitter_data, strava_data, steam_data,
                   oracle_coordinate, attachment_style, defense_mechanism,
                   fitting_self, fitting_ideal,
                   (spotify_data IS NOT NULL) AS has_spotify,
                   (twitter_data IS NOT NULL) AS has_twitter,
                   (strava_data IS NOT NULL) AS has_strava,
                   (steam_data IS NOT NULL) AS has_steam,
                   (oracle_coordinate IS NOT NULL) AS has_oracle
            FROM vibe_vectors WHERE user_id = $1
            """,
            target_id,
        )

        my_user = await conn.fetchrow(
            "SELECT display_name FROM users WHERE id = $1", user_id
        )
        their_user = await conn.fetchrow(
            "SELECT display_name FROM users WHERE id = $1", target_id
        )

        my_psych = await conn.fetchrow(
            "SELECT ipip_neo_scores, ecr_r_scores, love_language, "
            "sociosexual_orientation, values_cluster FROM user_psychometrics WHERE user_id = $1",
            user_id,
        )
        their_psych = await conn.fetchrow(
            "SELECT ipip_neo_scores, ecr_r_scores, love_language, "
            "sociosexual_orientation, values_cluster FROM user_psychometrics WHERE user_id = $1",
            target_id,
        )

    def parse_json(val):
        if val is None:
            return None
        return json.loads(val) if isinstance(val, str) else val

    def build_user_data(vibe, user_row):
        if not vibe:
            return None
        return {
            "display_name": user_row["display_name"] if user_row else None,
            "fitting_self": parse_json(vibe["fitting_self"]),
            "fitting_ideal": parse_json(vibe["fitting_ideal"]),
            "spotify_data": parse_json(vibe["spotify_data"]),
            "twitter_data": parse_json(vibe["twitter_data"]),
            "strava_data": parse_json(vibe["strava_data"]),
            "steam_data": parse_json(vibe["steam_data"]),
            "oracle_coordinate": parse_json(vibe["oracle_coordinate"]),
            "attachment_style": vibe["attachment_style"],
            "defense_mechanism": vibe["defense_mechanism"],
            "has_spotify": vibe["has_spotify"],
            "has_twitter": vibe["has_twitter"],
            "has_strava": vibe["has_strava"],
            "has_steam": vibe["has_steam"],
            "has_oracle": vibe["has_oracle"],
        }

    def build_psych(row):
        if not row:
            return None
        return {
            "ipip_neo_scores": parse_json(row["ipip_neo_scores"]),
            "ecr_r_scores": parse_json(row["ecr_r_scores"]),
            "love_language": row["love_language"],
            "sociosexual_orientation": row["sociosexual_orientation"],
            "values_cluster": row["values_cluster"],
        }

    from ..intake.router import _build_match_reason

    match_stub = {
        "score": 0,
        "attachment_style": their_vibe["attachment_style"] if their_vibe else None,
        "defense_mechanism": their_vibe["defense_mechanism"] if their_vibe else None,
    }

    similarity = 0.0
    try:
        from ..vector.service import find_nearest_users
        nearest = await find_nearest_users(str(user_id), top_k=10)
        for n in nearest:
            if n["user_id"] == str(target_id):
                similarity = n["score"]
                break
    except Exception:
        pass

    match_stub["score"] = similarity
    reason = _build_match_reason(match_stub, my_vibe, their_vibe)

    return {
        "similarity": similarity,
        "match_reason": reason,
        "self": build_user_data(my_vibe, my_user),
        "match": build_user_data(their_vibe, their_user),
        "psychometrics": {
            "self": build_psych(my_psych),
            "match": build_psych(their_psych),
        },
    }
