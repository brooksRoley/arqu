-- One-time purge of stale connect_tokens rows.
-- Depends on migration 025 (connect_tokens table, added in PR #8).
-- Safe to apply after 025: purges expired tokens (1h grace) and consumed tokens (24h grace).
DO $$
BEGIN
  IF EXISTS (
    SELECT FROM information_schema.tables
    WHERE table_schema = 'public' AND table_name = 'connect_tokens'
  ) THEN
    DELETE FROM connect_tokens
    WHERE expires_at < NOW() - INTERVAL '1 hour'
       OR (consumed_at IS NOT NULL AND consumed_at < NOW() - INTERVAL '24 hours');
  END IF;
END
$$;
