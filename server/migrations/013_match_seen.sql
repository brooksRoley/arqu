-- Track which mutual matches a user has already been notified about.

CREATE TABLE IF NOT EXISTS match_seen (
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    match_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    seen_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, match_id)
);
