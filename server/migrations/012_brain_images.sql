-- Brain image library — stores catalog of user-uploaded images
-- Vectors live in Pinecone "images" namespace; this table owns the metadata.

CREATE TABLE IF NOT EXISTS brain_images (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    blob_url    TEXT NOT NULL,
    filename    TEXT,
    description TEXT,          -- GPT-4o vision description used for embedding
    width       INTEGER,
    height      INTEGER,
    pinecone_id TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_brain_images_user ON brain_images(user_id);
CREATE INDEX IF NOT EXISTS idx_brain_images_pinecone ON brain_images(pinecone_id);
