-- Zeromind trance session data
ALTER TABLE vibe_vectors
  ADD COLUMN IF NOT EXISTS zeromind_data JSONB;
