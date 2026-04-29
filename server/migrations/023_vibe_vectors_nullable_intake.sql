-- Allow vibe_vectors rows to exist before intake completes,
-- so connector OAuth callbacks can persist provider data without
-- silently dropping it (UPDATE with no matching row).

ALTER TABLE vibe_vectors
    ALTER COLUMN attachment_style DROP NOT NULL,
    ALTER COLUMN defense_mechanism DROP NOT NULL;

INSERT INTO _migrations (filename) VALUES ('023_vibe_vectors_nullable_intake.sql')
ON CONFLICT (filename) DO NOTHING;
