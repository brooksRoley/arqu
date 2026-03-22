-- ═══════════════════════════════════════════════════════════════════
-- ChannelZero — Initial schema
-- Run against Neon: psql $DATABASE_URL -f server/migrations/001_init.sql
-- ═══════════════════════════════════════════════════════════════════

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ── Users ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email         TEXT UNIQUE NOT NULL,
    display_name  TEXT,
    password_hash TEXT NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ── Poll tokens (personality quiz results) ─────────────────────
CREATE TABLE IF NOT EXISTS poll_tokens (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID REFERENCES users(id) ON DELETE CASCADE,
    answers     JSONB NOT NULL,
    theme       TEXT NOT NULL,
    palette     JSONB NOT NULL,
    tone        TEXT,
    archetype   TEXT,
    keywords    TEXT[] DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_poll_tokens_user ON poll_tokens(user_id);

-- ── Journal entries ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS journal_entries (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID REFERENCES users(id) ON DELETE CASCADE,
    text          TEXT NOT NULL DEFAULT '',
    drawings      JSONB NOT NULL DEFAULT '[]',
    mood          TEXT,
    poll_token_id UUID REFERENCES poll_tokens(id) ON DELETE SET NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_journal_user_date ON journal_entries(user_id, created_at DESC);

-- ── Audio clips (metadata — blobs stay client-side or in object storage) ──
CREATE TABLE IF NOT EXISTS audio_clips (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entry_id    UUID REFERENCES journal_entries(id) ON DELETE CASCADE,
    blob_url    TEXT,
    duration_s  REAL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_audio_entry ON audio_clips(entry_id);

-- ── User API keys (encrypted at rest) ──────────────────────────
CREATE TABLE IF NOT EXISTS user_api_keys (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    provider        TEXT NOT NULL,
    encrypted_key   BYTEA NOT NULL,
    key_nonce       BYTEA NOT NULL,         -- AES-GCM nonce, unique per key
    key_hint        TEXT,                   -- last 4 chars, e.g. '...xK4m'
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_apikeys_user ON user_api_keys(user_id);

-- ── Migration tracking ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS _migrations (
    id         SERIAL PRIMARY KEY,
    filename   TEXT UNIQUE NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO _migrations (filename) VALUES ('001_init.sql')
ON CONFLICT (filename) DO NOTHING;
