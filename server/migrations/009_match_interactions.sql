-- ── Migration 009: Match interactions ────────────────────────────────────────
-- Tracks accept/reject decisions between matched users.
-- A "mutual match" occurs when both users have accepted each other.

CREATE TABLE IF NOT EXISTS match_interactions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    target_id   UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action      TEXT NOT NULL CHECK (action IN ('accept', 'reject')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (actor_id, target_id)
);

CREATE INDEX IF NOT EXISTS idx_match_actor  ON match_interactions(actor_id);
CREATE INDEX IF NOT EXISTS idx_match_target ON match_interactions(target_id);

-- Convenience view: mutual matches (both sides accepted)
CREATE OR REPLACE VIEW mutual_matches AS
SELECT
    a.actor_id  AS user_a,
    a.target_id AS user_b,
    GREATEST(a.created_at, b.created_at) AS matched_at
FROM match_interactions a
JOIN match_interactions b
    ON  a.actor_id  = b.target_id
    AND a.target_id = b.actor_id
WHERE a.action = 'accept'
  AND b.action = 'accept'
  AND a.actor_id < a.target_id;  -- deduplicate: only one row per pair
