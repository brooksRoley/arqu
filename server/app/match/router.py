"""Match interaction routes — accept/reject + mutual match detection."""

from __future__ import annotations

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
