-- ═══════════════════════════════════════════════════════════════════
-- ChannelZero — Intake pipeline tables
-- Encrypted shadow logs + vibe vectors for psychoanalytic profiling
-- ═══════════════════════════════════════════════════════════════════

-- ── Intake shadow logs (encrypted confessional text) ─────────────
-- Raw text is NEVER stored in plaintext. AES-256-GCM encrypted at rest.
CREATE TABLE IF NOT EXISTS intake_shadow_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    encrypted_text  BYTEA NOT NULL,
    text_nonce      BYTEA NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_intake_logs_user ON intake_shadow_logs(user_id);

-- ── Vibe vectors (derived psychological profile) ─────────────────
-- One per user, upserted on each intake session.
CREATE TABLE IF NOT EXISTS vibe_vectors (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    attachment_style    TEXT NOT NULL,
    defense_mechanism   TEXT NOT NULL,
    readiness_score     INTEGER NOT NULL DEFAULT 0,
    poll_theme          TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_vibe_user ON vibe_vectors(user_id);

-- ── Migration tracking ───────────────────────────────────────────
INSERT INTO _migrations (filename) VALUES ('002_intake.sql')
ON CONFLICT (filename) DO NOTHING;
