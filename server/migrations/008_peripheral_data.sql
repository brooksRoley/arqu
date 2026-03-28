-- 008_peripheral_data.sql
-- Add JSONB columns on vibe_vectors for each peripheral data connector,
-- plus identity columns on users for Steam and Letterboxd.

ALTER TABLE vibe_vectors ADD COLUMN IF NOT EXISTS gcal_data JSONB;
ALTER TABLE vibe_vectors ADD COLUMN IF NOT EXISTS twitter_data JSONB;
ALTER TABLE vibe_vectors ADD COLUMN IF NOT EXISTS costar_data JSONB;
ALTER TABLE vibe_vectors ADD COLUMN IF NOT EXISTS letterboxd_data JSONB;
ALTER TABLE vibe_vectors ADD COLUMN IF NOT EXISTS steam_data JSONB;

ALTER TABLE users ADD COLUMN IF NOT EXISTS steam_id TEXT UNIQUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS letterboxd_username TEXT;
