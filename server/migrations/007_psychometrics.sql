CREATE TABLE IF NOT EXISTS user_psychometrics (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    scorable_responses TEXT NOT NULL,
    ipip_neo_scores JSONB,
    ecr_r_scores JSONB,
    love_language TEXT,
    sociosexual_orientation TEXT,
    values_cluster TEXT,
    narrative TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
