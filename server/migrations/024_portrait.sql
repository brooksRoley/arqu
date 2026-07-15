-- Integrated Portrait: one stored cross-provider narrative per user.
-- portrait                    — the Portrait JSON (headline, sections[], throughline)
-- portrait_generated_at       — when it was last generated
-- portrait_source_providers   — the connected-provider set it was built from,
--                               compared against the live set to compute staleness
ALTER TABLE vibe_vectors
  ADD COLUMN IF NOT EXISTS portrait JSONB,
  ADD COLUMN IF NOT EXISTS portrait_generated_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS portrait_source_providers TEXT[];
