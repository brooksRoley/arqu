-- ── Migration 006: Strava provider identity on users ────────────────────────
-- Allow linking Strava athlete ID to user accounts.

ALTER TABLE users ADD COLUMN IF NOT EXISTS strava_id TEXT UNIQUE;

-- Add strava_data column to vibe_vectors for somatic profile storage
ALTER TABLE vibe_vectors ADD COLUMN IF NOT EXISTS strava_data JSONB;

INSERT INTO _migrations (filename) VALUES ('006_strava_provider.sql')
ON CONFLICT (filename) DO NOTHING;
