-- 016_fitting_data.sql
-- Add avatar data columns for the fitting ritual (self-image + ideal-partner)

ALTER TABLE vibe_vectors
  ADD COLUMN IF NOT EXISTS fitting_self JSONB DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS fitting_ideal JSONB DEFAULT NULL;
