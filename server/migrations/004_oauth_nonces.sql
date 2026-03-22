-- ── Migration 004: OAuth nonce replay protection ────────────────────────────
-- One-time-use nonces for OAuth state JWTs. UNIQUE constraint prevents replay.

CREATE TABLE IF NOT EXISTS _oauth_nonces (
    nonce        TEXT PRIMARY KEY,
    consumed_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Periodically clean up expired nonces (older than 10 minutes).
-- This can be done by a cron or by the app itself; the nonces are
-- only security-relevant within their 600-second JWT TTL window.
CREATE INDEX IF NOT EXISTS idx_oauth_nonces_consumed ON _oauth_nonces(consumed_at);

-- ── Karma ledger hardening ──────────────────────────────────────────────────
-- Prevent duplicate POS_HANDSHAKE events within a 60-second window.
-- The app should enforce this, but the DB constraint is a safety net.
ALTER TABLE karma_ledger
    ADD COLUMN IF NOT EXISTS idempotency_key TEXT UNIQUE;

INSERT INTO _migrations (filename) VALUES ('004_oauth_nonces.sql')
ON CONFLICT (filename) DO NOTHING;
