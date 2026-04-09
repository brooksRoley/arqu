"""Analytics routes — admin dashboard data + connector feedback."""

from __future__ import annotations

import json
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from ..auth.deps import get_current_user_id, require_admin
from ..db import get_conn

router = APIRouter()

VALID_PROVIDERS = {"spotify", "twitter", "google", "strava", "steam", "letterboxd", "costar"}


# ── Feedback models ──────────────────────────────────────────────────────────

class FeedbackRequest(BaseModel):
    provider: str
    rating: int          # 1–5
    tags: list[str] = []


class EventRequest(BaseModel):
    event: str
    metadata: dict = {}


# ── User-facing: log a session event ────────────────────────────────────────

@router.post("/event", status_code=204)
async def log_event(
    body: EventRequest,
    user_id: UUID = Depends(get_current_user_id),
):
    """Log a funnel event for the current user."""
    async with get_conn() as conn:
        await conn.execute(
            """
            INSERT INTO session_events (user_id, event, metadata)
            VALUES ($1, $2, $3::jsonb)
            """,
            user_id, body.event, json.dumps(body.metadata),
        )


# ── User-facing: submit connector satisfaction ───────────────────────────────

@router.post("/feedback/connector", status_code=204)
async def submit_connector_feedback(
    body: FeedbackRequest,
    user_id: UUID = Depends(get_current_user_id),
):
    """Upsert a satisfaction rating for a connected provider."""
    if body.provider not in VALID_PROVIDERS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown provider: {body.provider}")
    if not (1 <= body.rating <= 5):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rating must be 1–5")

    async with get_conn() as conn:
        await conn.execute(
            """
            INSERT INTO connector_feedback (user_id, provider, rating, tags)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (user_id, provider) DO UPDATE SET
                rating     = EXCLUDED.rating,
                tags       = EXCLUDED.tags,
                updated_at = now()
            """,
            user_id, body.provider, body.rating, body.tags,
        )


# ── Admin: paginated user list with heuristics ───────────────────────────────

@router.get("/users")
async def admin_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    _: UUID = Depends(require_admin),
):
    """Return all users with their psychological heuristics. Admin only."""
    offset = (page - 1) * per_page

    async with get_conn() as conn:
        total = await conn.fetchval("SELECT COUNT(*) FROM users")

        rows = await conn.fetch(
            """
            SELECT
                u.id,
                u.email,
                u.display_name,
                u.created_at,
                u.is_admin,

                vv.attachment_style,
                vv.defense_mechanism,
                vv.readiness_score,
                vv.poll_theme,

                pt.archetype,
                pt.tone,
                pt.keywords,

                (
                    SELECT array_agg(provider ORDER BY provider)
                    FROM oauth_tokens ot WHERE ot.user_id = u.id
                ) AS connected_providers,

                (SELECT COUNT(*) FROM oauth_tokens ot WHERE ot.user_id = u.id)
                    AS connector_count,

                (SELECT COALESCE(SUM(karma_delta), 0)
                 FROM karma_ledger kl WHERE kl.user_id = u.id)
                    AS karma_total,

                (SELECT COUNT(*) FROM match_interactions mi
                 WHERE mi.actor_id = u.id AND mi.action = 'accept')
                    AS matches_accepted,

                (SELECT COUNT(*) FROM match_interactions mi
                 WHERE mi.actor_id = u.id AND mi.action = 'reject')
                    AS matches_rejected,

                (SELECT COUNT(*) FROM match_interactions mi
                 WHERE mi.target_id = u.id AND mi.action = 'accept')
                    AS received_accepts,

                (SELECT COUNT(*) FROM journal_entries je WHERE je.user_id = u.id)
                    AS journal_entry_count,

                (SELECT COUNT(*) FROM messages m WHERE m.sender_id = u.id)
                    AS messages_sent,

                (vv.user_id IS NOT NULL)  AS has_vibe_vector,
                (pm.user_id IS NOT NULL)  AS has_psychometrics,

                (vv.spotify_data     IS NOT NULL) AS has_spotify,
                (vv.twitter_data     IS NOT NULL) AS has_twitter,
                (vv.gcal_data        IS NOT NULL) AS has_gcal,
                (vv.costar_data      IS NOT NULL) AS has_costar,
                (vv.letterboxd_data  IS NOT NULL) AS has_letterboxd,
                (vv.steam_data       IS NOT NULL) AS has_steam

            FROM users u
            LEFT JOIN vibe_vectors vv ON vv.user_id = u.id
            LEFT JOIN poll_tokens  pt ON pt.user_id = u.id
            LEFT JOIN user_psychometrics pm ON pm.user_id = u.id
            ORDER BY u.created_at DESC
            LIMIT $1 OFFSET $2
            """,
            per_page, offset,
        )

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "users": [dict(r) for r in rows],
    }


# ── Admin: conversion funnel ─────────────────────────────────────────────────

@router.get("/funnel")
async def admin_funnel(_: UUID = Depends(require_admin)):
    """Return step-by-step conversion counts across the user funnel."""
    async with get_conn() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                COUNT(*)                                                  AS total_registered,
                COUNT(*) FILTER (WHERE pt.user_id IS NOT NULL)            AS completed_poll,
                COUNT(*) FILTER (WHERE vv.user_id IS NOT NULL)            AS has_vibe_vector,
                COUNT(*) FILTER (WHERE ot.provider_count > 0)             AS connected_any,
                COUNT(*) FILTER (WHERE ot.provider_count >= 2)            AS connected_2plus,
                COUNT(*) FILTER (WHERE pm.user_id IS NOT NULL)            AS completed_psychometrics,
                COUNT(*) FILTER (WHERE mi.actor_id IS NOT NULL)           AS played_game,
                COUNT(*) FILTER (WHERE mm.user_id IS NOT NULL)            AS got_mutual_match,
                COUNT(*) FILTER (WHERE msg.sender_id IS NOT NULL)         AS sent_message
            FROM users u
            LEFT JOIN poll_tokens pt ON pt.user_id = u.id
            LEFT JOIN vibe_vectors vv ON vv.user_id = u.id
            LEFT JOIN user_psychometrics pm ON pm.user_id = u.id
            LEFT JOIN (
                SELECT user_id, COUNT(DISTINCT provider) AS provider_count
                FROM oauth_tokens GROUP BY user_id
            ) ot ON ot.user_id = u.id
            LEFT JOIN (
                SELECT DISTINCT actor_id FROM match_interactions
            ) mi ON mi.actor_id = u.id
            LEFT JOIN (
                SELECT DISTINCT
                    CASE WHEN actor_id < target_id THEN actor_id ELSE target_id END AS user_id
                FROM match_interactions a
                JOIN match_interactions b
                    ON a.actor_id = b.target_id AND a.target_id = b.actor_id
                WHERE a.action = 'accept' AND b.action = 'accept'
            ) mm ON mm.user_id = u.id
            LEFT JOIN (
                SELECT DISTINCT sender_id FROM messages
            ) msg ON msg.sender_id = u.id
            """
        )

    data = dict(row)
    total = data["total_registered"] or 1  # avoid division by zero

    steps = [
        ("registered",            data["total_registered"]),
        ("completed_poll",        data["completed_poll"]),
        ("connected_any",         data["connected_any"]),
        ("connected_2plus",       data["connected_2plus"]),
        ("has_vibe_vector",       data["has_vibe_vector"]),
        ("completed_psychometrics", data["completed_psychometrics"]),
        ("played_game",           data["played_game"]),
        ("got_mutual_match",      data["got_mutual_match"]),
        ("sent_message",          data["sent_message"]),
    ]

    return [
        {"step": name, "count": count, "pct": round(count / total * 100, 1)}
        for name, count in steps
    ]


# ── Admin: per-connector stats ───────────────────────────────────────────────

@router.get("/connectors")
async def admin_connectors(_: UUID = Depends(require_admin)):
    """Return connection rate, drop rate, and avg satisfaction per provider."""
    async with get_conn() as conn:
        total_users = await conn.fetchval("SELECT COUNT(*) FROM users")

        connection_rows = await conn.fetch(
            """
            SELECT provider, COUNT(DISTINCT user_id) AS connected_count
            FROM oauth_tokens
            GROUP BY provider
            ORDER BY provider
            """
        )

        feedback_rows = await conn.fetch(
            """
            SELECT
                provider,
                COUNT(*)                          AS feedback_count,
                ROUND(AVG(rating)::numeric, 2)    AS avg_rating,
                array_agg(tags)                   AS tag_arrays
            FROM connector_feedback
            GROUP BY provider
            ORDER BY provider
            """
        )

    connected = {r["provider"]: r["connected_count"] for r in connection_rows}
    fb_map = {r["provider"]: dict(r) for r in feedback_rows}

    # Flatten tag arrays and deduplicate
    def flatten_tags(tag_arrays):
        seen = set()
        result = []
        for arr in (tag_arrays or []):
            for t in (arr or []):
                if t not in seen:
                    seen.add(t)
                    result.append(t)
        return result

    all_providers = sorted(VALID_PROVIDERS)
    results = []
    for p in all_providers:
        conn_count = connected.get(p, 0)
        fb = fb_map.get(p, {})
        results.append({
            "provider": p,
            "connected_count": conn_count,
            "connection_rate_pct": round(conn_count / (total_users or 1) * 100, 1),
            "feedback_count": fb.get("feedback_count", 0),
            "avg_rating": float(fb["avg_rating"]) if fb.get("avg_rating") is not None else None,
            "top_tags": flatten_tags(fb.get("tag_arrays")),
        })

    return results


# ── Admin: recent session events ─────────────────────────────────────────────

@router.get("/events")
async def admin_events(
    event: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    _: UUID = Depends(require_admin),
):
    """Return recent session events, optionally filtered by event type."""
    async with get_conn() as conn:
        if event:
            rows = await conn.fetch(
                """
                SELECT se.id, se.user_id, u.email, u.display_name,
                       se.event, se.metadata, se.created_at
                FROM session_events se
                LEFT JOIN users u ON u.id = se.user_id
                WHERE se.event = $1
                ORDER BY se.created_at DESC LIMIT $2
                """,
                event, limit,
            )
        else:
            rows = await conn.fetch(
                """
                SELECT se.id, se.user_id, u.email, u.display_name,
                       se.event, se.metadata, se.created_at
                FROM session_events se
                LEFT JOIN users u ON u.id = se.user_id
                ORDER BY se.created_at DESC LIMIT $1
                """,
                limit,
            )

    return [dict(r) for r in rows]
