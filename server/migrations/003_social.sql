-- ── Migration 003: Social layer ──────────────────────────────────────────────
-- oauth_tokens, karma_ledger, venues, and Spotify data on vibe_vectors.

-- OAuth provider tokens (encrypted at rest, same pattern as user API keys)
CREATE TABLE IF NOT EXISTS oauth_tokens (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                 UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider                TEXT NOT NULL,                  -- 'spotify' | 'twitter' | 'google'
    encrypted_access_token  BYTEA NOT NULL,
    access_nonce            BYTEA NOT NULL,
    encrypted_refresh_token BYTEA,
    refresh_nonce           BYTEA,
    expires_at              TIMESTAMPTZ,
    scope                   TEXT,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, provider)
);
CREATE INDEX IF NOT EXISTS idx_oauth_user ON oauth_tokens(user_id);

-- Karma ledger: append-only event log; current score is a rolling SUM
CREATE TABLE IF NOT EXISTS karma_ledger (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_type      TEXT NOT NULL,      -- 'POS_HANDSHAKE' | 'GHOSTED' | 'CO_OP_MODE' | 'ACCOUNT_CREATION' ...
    karma_delta     INTEGER NOT NULL,
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_karma_user ON karma_ledger(user_id);

-- Physical venue anchors for POS karma handshakes
CREATE TABLE IF NOT EXISTS venues (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    gps_lat         NUMERIC(10, 7),
    gps_lng         NUMERIC(10, 7),
    discount_tier   TEXT,               -- 'FREE_APPETIZER' | 'BOGO_TOKENS' | '15_PERCENT_OFF'
    qr_seed         TEXT UNIQUE NOT NULL,
    active          BOOLEAN NOT NULL DEFAULT true,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Attach Spotify profile data to the vibe vector row
ALTER TABLE vibe_vectors
    ADD COLUMN IF NOT EXISTS spotify_data JSONB;
