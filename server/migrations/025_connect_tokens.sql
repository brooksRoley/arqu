-- Short-lived single-use tokens for OAuth connect flows.
-- Replaces passing the full 24-hour JWT as a query parameter (?token=...)
-- which leaks to server logs, browser history, and Referer headers.
CREATE TABLE IF NOT EXISTS connect_tokens (
    token       TEXT PRIMARY KEY,
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at  TIMESTAMPTZ NOT NULL,
    consumed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS connect_tokens_expires_at_idx ON connect_tokens (expires_at);
