"""Encrypted mutual-match messaging."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..auth.deps import get_current_user_id
from ..db import get_conn
from ..llm.encryption import encrypt_api_key, decrypt_api_key
from .models import MessageOut, SendRequest, ThreadSummary

router = APIRouter()

PAGE_SIZE = 40


def _thread_id(a: UUID, b: UUID) -> str:
    """Stable lexicographic key for a user pair — same regardless of who queries."""
    ids = sorted([str(a), str(b)])
    return f"{ids[0]}_{ids[1]}"


async def _assert_mutual_match(conn, user_id: UUID, other_id: UUID) -> None:
    row = await conn.fetchrow(
        """
        SELECT 1
        FROM match_interactions a
        JOIN match_interactions b
            ON  a.actor_id  = b.target_id
            AND a.target_id = b.actor_id
        WHERE a.action = 'accept' AND b.action = 'accept'
          AND a.actor_id = $1 AND a.target_id = $2
        """,
        user_id, other_id,
    )
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Messaging requires a mutual match",
        )


def _decrypt_body(row) -> str:
    try:
        return decrypt_api_key(bytes(row["encrypted_body"]), bytes(row["body_nonce"]))
    except Exception:
        return "[decryption error]"


# ── Send ────────────────────────────────────────────────────────────────────

@router.post("/send", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
async def send_message(
    body: SendRequest,
    user_id: UUID = Depends(get_current_user_id),
):
    if body.recipient_id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot message yourself",
        )

    thread = _thread_id(user_id, body.recipient_id)
    encrypted, nonce = encrypt_api_key(body.body)

    async with get_conn() as conn:
        await _assert_mutual_match(conn, user_id, body.recipient_id)

        row = await conn.fetchrow(
            """
            INSERT INTO messages
                (thread_id, sender_id, recipient_id, encrypted_body, body_nonce)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, sender_id, recipient_id, read_at, created_at
            """,
            thread, user_id, body.recipient_id, encrypted, nonce,
        )

    return MessageOut(
        id=str(row["id"]),
        sender_id=str(row["sender_id"]),
        recipient_id=str(row["recipient_id"]),
        body=body.body,
        read_at=row["read_at"].isoformat() if row["read_at"] else None,
        created_at=row["created_at"].isoformat(),
    )


# ── Thread history ──────────────────────────────────────────────────────────

@router.get("/thread/{other_user_id}", response_model=list[MessageOut])
async def get_thread(
    other_user_id: UUID,
    before: str | None = Query(None, description="ISO timestamp — fetch messages older than this"),
    user_id: UUID = Depends(get_current_user_id),
):
    thread = _thread_id(user_id, other_user_id)

    async with get_conn() as conn:
        await _assert_mutual_match(conn, user_id, other_user_id)

        # Mark incoming messages as read
        await conn.execute(
            """
            UPDATE messages
               SET read_at = now()
             WHERE thread_id = $1
               AND recipient_id = $2
               AND read_at IS NULL
            """,
            thread, user_id,
        )

        if before:
            rows = await conn.fetch(
                """
                SELECT id, sender_id, recipient_id, encrypted_body, body_nonce, read_at, created_at
                  FROM messages
                 WHERE thread_id = $1
                   AND created_at < $2::timestamptz
                 ORDER BY created_at DESC
                 LIMIT $3
                """,
                thread, before, PAGE_SIZE,
            )
        else:
            rows = await conn.fetch(
                """
                SELECT id, sender_id, recipient_id, encrypted_body, body_nonce, read_at, created_at
                  FROM messages
                 WHERE thread_id = $1
                 ORDER BY created_at DESC
                 LIMIT $2
                """,
                thread, PAGE_SIZE,
            )

    return [
        MessageOut(
            id=str(r["id"]),
            sender_id=str(r["sender_id"]),
            recipient_id=str(r["recipient_id"]),
            body=_decrypt_body(r),
            read_at=r["read_at"].isoformat() if r["read_at"] else None,
            created_at=r["created_at"].isoformat(),
        )
        for r in reversed(rows)  # oldest first for display
    ]


# ── Thread list ─────────────────────────────────────────────────────────────

@router.get("/threads", response_model=list[ThreadSummary])
async def list_threads(user_id: UUID = Depends(get_current_user_id)):
    """
    All mutual matches that have at least one message, sorted by last activity.
    Also returns unread count per thread.
    """
    async with get_conn() as conn:
        # Get all mutual matches for this user
        mutual_rows = await conn.fetch(
            """
            SELECT
                CASE WHEN a.actor_id = $1 THEN a.target_id ELSE a.actor_id END AS other_id
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

        results: list[ThreadSummary] = []
        for mr in mutual_rows:
            other_id = mr["other_id"]
            thread = _thread_id(user_id, other_id)

            # Last message + unread count
            stats = await conn.fetchrow(
                """
                SELECT
                    MAX(created_at)                                         AS last_at,
                    COUNT(*)                                                AS total,
                    COUNT(*) FILTER (WHERE recipient_id = $2 AND read_at IS NULL) AS unread
                FROM messages
                WHERE thread_id = $1
                """,
                thread, user_id,
            )

            if stats["total"] == 0:
                continue  # no messages yet — skip

            # Last message body
            last_row = await conn.fetchrow(
                """
                SELECT encrypted_body, body_nonce
                  FROM messages
                 WHERE thread_id = $1
                 ORDER BY created_at DESC
                 LIMIT 1
                """,
                thread,
            )
            last_text = _decrypt_body(last_row) if last_row else None

            # Other user's display name
            user_row = await conn.fetchrow(
                "SELECT display_name FROM users WHERE id = $1", other_id
            )

            results.append(ThreadSummary(
                other_user_id=str(other_id),
                other_user_name=user_row["display_name"] if user_row else "Unknown",
                last_message=last_text,
                last_message_at=stats["last_at"].isoformat() if stats["last_at"] else None,
                unread_count=int(stats["unread"]),
            ))

        results.sort(key=lambda t: t.last_message_at or "", reverse=True)
        return results


# ── Unread count only (cheap poll) ──────────────────────────────────────────

@router.get("/unread")
async def unread_count(user_id: UUID = Depends(get_current_user_id)):
    """Total unread messages across all threads. Used by NavBar badge."""
    async with get_conn() as conn:
        row = await conn.fetchrow(
            """
            SELECT COUNT(*) AS n
              FROM messages
             WHERE recipient_id = $1
               AND read_at IS NULL
            """,
            user_id,
        )
    return {"unread": int(row["n"])}
