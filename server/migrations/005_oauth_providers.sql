-- ── Migration 005: OAuth provider identities on users ────────────────────────
-- Allow users to sign in via Google or X without a password.

-- Provider identity columns
ALTER TABLE users ADD COLUMN IF NOT EXISTS google_id TEXT UNIQUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS x_id      TEXT UNIQUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url TEXT;

-- OAuth users don't set a password — make hash nullable
ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL;

INSERT INTO _migrations (filename) VALUES ('005_oauth_providers.sql')
ON CONFLICT (filename) DO NOTHING;
