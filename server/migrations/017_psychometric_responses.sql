-- 017_psychometric_responses.sql
-- Individual psychometric item responses for the microdose system

CREATE TABLE IF NOT EXISTS psychometric_responses (
    user_id UUID NOT NULL REFERENCES users(id),
    item_id TEXT NOT NULL,
    value INT NOT NULL,
    connector_context TEXT,
    trance_coherence FLOAT,
    session_duration_ms INT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, item_id)
);
