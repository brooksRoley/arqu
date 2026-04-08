-- ── Migration 010: Mutual-match messaging ──────────────────────────────────
-- Encrypted message threads, gated to mutual matches only.
-- thread_id is a stable TEXT key: LEAST(uuid_a, uuid_b) || '_' || GREATEST(uuid_a, uuid_b)
-- Encryption: AES-256-GCM matching the shadow_log / oauth_token pattern.

CREATE TABLE IF NOT EXISTS messages (
    id             UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id      TEXT        NOT NULL,
    sender_id      UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    recipient_id   UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    encrypted_body BYTEA       NOT NULL,
    body_nonce     BYTEA       NOT NULL,
    read_at        TIMESTAMPTZ,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (sender_id <> recipient_id)
);

CREATE INDEX IF NOT EXISTS idx_messages_thread
    ON messages(thread_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_messages_recipient_unread
    ON messages(recipient_id, read_at)
    WHERE read_at IS NULL;
