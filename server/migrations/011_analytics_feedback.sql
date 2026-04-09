-- ── Migration 011: Analytics & connector feedback ────────────────────────────
-- Adds admin flag, connector satisfaction ratings, and funnel event log.

-- Admin flag on users
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN NOT NULL DEFAULT FALSE;

-- ── Connector feedback ────────────────────────────────────────────────────────
-- One rating per user per provider (upsertable).
-- Tags are free chips: 'felt_relevant', 'too_invasive', 'didnt_add_value', 'surprised_me'
CREATE TABLE IF NOT EXISTS connector_feedback (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider    TEXT        NOT NULL CHECK (provider IN (
                                'spotify','twitter','google','strava',
                                'steam','letterboxd','costar')),
    rating      SMALLINT    NOT NULL CHECK (rating BETWEEN 1 AND 5),
    tags        TEXT[]      NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, provider)
);

CREATE INDEX IF NOT EXISTS idx_connector_feedback_provider
    ON connector_feedback(provider, rating);

-- ── Session events (funnel tracking) ─────────────────────────────────────────
-- Append-only. user_id nullable so anonymous pre-registration events can land.
-- event values: registered | poll_completed | connector_attempted | connector_connected
--               connector_dropped | synthesis_triggered | game_started | match_made
--               message_sent
CREATE TABLE IF NOT EXISTS session_events (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID        REFERENCES users(id) ON DELETE SET NULL,
    event       TEXT        NOT NULL,
    metadata    JSONB       NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_session_events_user
    ON session_events(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_session_events_type
    ON session_events(event, created_at DESC);

INSERT INTO _migrations (filename) VALUES ('011_analytics_feedback.sql')
ON CONFLICT (filename) DO NOTHING;
