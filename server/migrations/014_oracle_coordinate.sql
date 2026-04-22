-- Oracle coordinate persistence
ALTER TABLE vibe_vectors
  ADD COLUMN IF NOT EXISTS oracle_coordinate JSONB,
  ADD COLUMN IF NOT EXISTS oracle_synthesized_at TIMESTAMPTZ;
