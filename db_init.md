# Neon DB Initialization & Seeding
> "Before the matches can burn, the earth must be packed."

This file contains the raw PostgreSQL schema for our Neon serverless database, establishing the Vibe Economy. We seed it with the foundational venues and a handful of test subjects to calibrate the LLM routing.

## 1. The Schema Execution (`schema.sql`)

```sql
-- Core Identity
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    base_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_shadowbanned BOOLEAN DEFAULT FALSE
);

-- The Soul's Architecture
CREATE TABLE vibe_vectors (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    spotify_valence NUMERIC(4,3),
    spotify_danceability NUMERIC(4,3),
    twitter_dominance NUMERIC(4,3),
    humor_darkness NUMERIC(4,3),
    raw_llm_summary TEXT,
    last_calibrated TIMESTAMP WITH TIME ZONE,
    PRIMARY KEY (user_id)
);

-- The Gamification Ledger
CREATE TABLE karma_ledger (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL, -- 'POS_HANDSHAKE', 'GHOSTED', 'CO_OP_MODE'
    karma_delta INTEGER NOT NULL,
    event_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- The Physical Anchors
CREATE TABLE venues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    gps_lat NUMERIC(10,7),
    gps_long NUMERIC(10,7),
    discount_tier VARCHAR(50), -- '15_PERCENT_OFF', 'FREE_APPETIZER'
    qr_seed VARCHAR(255) UNIQUE NOT NULL
);