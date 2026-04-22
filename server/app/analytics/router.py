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


# ── Admin: match rate trends ──────────────────────────────────────────────────

@router.get("/match-trends")
async def admin_match_trends(_: UUID = Depends(require_admin)):
    """Return match rate trends for the last 7 and 30 days."""
    async with get_conn() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                -- Users who played the game (made any interaction)
                COUNT(DISTINCT mi.actor_id) FILTER (
                    WHERE mi.created_at >= now() - interval '7 days'
                ) AS players_7d,
                COUNT(DISTINCT mi.actor_id) FILTER (
                    WHERE mi.created_at >= now() - interval '30 days'
                ) AS players_30d,

                -- Users who got a mutual match
                COUNT(DISTINCT mm.user_id) FILTER (
                    WHERE mm.matched_at >= now() - interval '7 days'
                ) AS matched_7d,
                COUNT(DISTINCT mm.user_id) FILTER (
                    WHERE mm.matched_at >= now() - interval '30 days'
                ) AS matched_30d

            FROM match_interactions mi
            FULL OUTER JOIN (
                SELECT
                    CASE WHEN a.actor_id < a.target_id THEN a.actor_id ELSE a.target_id END AS user_id,
                    GREATEST(a.created_at, b.created_at) AS matched_at
                FROM match_interactions a
                JOIN match_interactions b
                    ON  a.actor_id  = b.target_id
                    AND a.target_id = b.actor_id
                WHERE a.action = 'accept' AND b.action = 'accept'
                  AND a.actor_id < a.target_id
            ) mm ON TRUE
            """
        )

    data = dict(row)
    p7 = data["players_7d"] or 0
    p30 = data["players_30d"] or 0
    m7 = data["matched_7d"] or 0
    m30 = data["matched_30d"] or 0

    return {
        "seven_day": {
            "players": p7,
            "matched": m7,
            "rate_pct": round(m7 / p7 * 100, 1) if p7 > 0 else 0,
        },
        "thirty_day": {
            "players": p30,
            "matched": m30,
            "rate_pct": round(m30 / p30 * 100, 1) if p30 > 0 else 0,
        },
    }


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


# ── Admin: Spotify profiles (paginated) ─────────────────────────────────────

@router.get("/spotify-profiles")
async def admin_spotify_profiles(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    _: UUID = Depends(require_admin),
):
    """Return users with Spotify profile data. Admin only."""
    offset = (page - 1) * per_page

    async with get_conn() as conn:
        total = await conn.fetchval(
            "SELECT COUNT(*) FROM vibe_vectors WHERE spotify_data IS NOT NULL"
        )
        rows = await conn.fetch(
            """
            SELECT
                u.id, u.email, u.display_name,
                vv.spotify_data
            FROM vibe_vectors vv
            JOIN users u ON u.id = vv.user_id
            WHERE vv.spotify_data IS NOT NULL
            ORDER BY u.created_at DESC
            LIMIT $1 OFFSET $2
            """,
            per_page, offset,
        )

    profiles = []
    for r in rows:
        data = r["spotify_data"]
        parsed = json.loads(data) if isinstance(data, str) else data
        profiles.append({
            "user_id": str(r["id"]),
            "email": r["email"],
            "display_name": r["display_name"],
            "top_artists": parsed.get("top_artists", []),
            "genres": parsed.get("genres", []),
            "audio_avg": parsed.get("audio_avg", {}),
        })

    return {"total": total, "page": page, "per_page": per_page, "profiles": profiles}


# ── Admin: archetype distribution ────────────────────────────────────────────

@router.get("/archetypes")
async def admin_archetypes(_: UUID = Depends(require_admin)):
    """Return archetype distribution across all users."""
    async with get_conn() as conn:
        rows = await conn.fetch(
            """
            SELECT pt.archetype, COUNT(*) AS count
            FROM poll_tokens pt
            WHERE pt.archetype IS NOT NULL
            GROUP BY pt.archetype
            ORDER BY count DESC
            LIMIT 8
            """
        )
        total = await conn.fetchval(
            "SELECT COUNT(*) FROM poll_tokens WHERE archetype IS NOT NULL"
        )
    return {
        "total": total or 0,
        "archetypes": [{"archetype": r["archetype"], "count": r["count"]} for r in rows],
    }


# ── Admin: attachment style breakdown ────────────────────────────────────────

@router.get("/attachment-styles")
async def admin_attachment_styles(_: UUID = Depends(require_admin)):
    """Return attachment style breakdown across all users."""
    async with get_conn() as conn:
        rows = await conn.fetch(
            """
            SELECT attachment_style, COUNT(*) AS count
            FROM vibe_vectors
            WHERE attachment_style IS NOT NULL
            GROUP BY attachment_style
            ORDER BY count DESC
            """
        )
        total = await conn.fetchval(
            "SELECT COUNT(*) FROM vibe_vectors WHERE attachment_style IS NOT NULL"
        )
    return {
        "total": total or 0,
        "styles": [{"style": r["attachment_style"], "count": r["count"]} for r in rows],
    }


# ── Admin: connector depth histogram ────────────────────────────────────────

@router.get("/connector-depth")
async def admin_connector_depth(_: UUID = Depends(require_admin)):
    """Return histogram of users by number of connected providers."""
    async with get_conn() as conn:
        rows = await conn.fetch(
            """
            SELECT bucket, COUNT(*) AS count FROM (
                SELECT u.id,
                    LEAST((SELECT COUNT(*) FROM oauth_tokens ot WHERE ot.user_id = u.id), 3) AS bucket
                FROM users u
            ) sub
            GROUP BY bucket
            ORDER BY bucket
            """
        )
    # Ensure all buckets 0-3 present
    histogram = {0: 0, 1: 0, 2: 0, 3: 0}
    for r in rows:
        histogram[r["bucket"]] = r["count"]
    return {"histogram": [{"connectors": k, "count": v} for k, v in sorted(histogram.items())]}


# ── Admin: Psychometric profiles (paginated) ────────────────────────────────

@router.get("/psychometrics")
async def admin_psychometrics(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    _: UUID = Depends(require_admin),
):
    """Return users with psychometric data. Admin only."""
    offset = (page - 1) * per_page

    async with get_conn() as conn:
        total = await conn.fetchval("SELECT COUNT(*) FROM user_psychometrics")
        rows = await conn.fetch(
            """
            SELECT
                u.id, u.email, u.display_name,
                pm.love_language, pm.sociosexual_orientation,
                pm.values_cluster, pm.narrative,
                pm.ipip_neo_scores, pm.ecr_r_scores,
                pm.created_at
            FROM user_psychometrics pm
            JOIN users u ON u.id = pm.user_id
            ORDER BY pm.created_at DESC
            LIMIT $1 OFFSET $2
            """,
            per_page, offset,
        )

    profiles = []
    for r in rows:
        ipip = r["ipip_neo_scores"]
        ecr = r["ecr_r_scores"]
        profiles.append({
            "user_id": str(r["id"]),
            "email": r["email"],
            "display_name": r["display_name"],
            "love_language": r["love_language"],
            "sociosexual_orientation": r["sociosexual_orientation"],
            "values_cluster": r["values_cluster"],
            "narrative": r["narrative"],
            "ipip_neo_scores": json.loads(ipip) if isinstance(ipip, str) else ipip,
            "ecr_r_scores": json.loads(ecr) if isinstance(ecr, str) else ecr,
            "created_at": str(r["created_at"]),
        })

    return {"total": total, "page": page, "per_page": per_page, "profiles": profiles}
