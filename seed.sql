-- Injecting the Anchors (The Venues)
INSERT INTO venues (id, name, gps_lat, gps_long, discount_tier, qr_seed) VALUES
('v1_bodega', 'Javier’s Bodega and Tapas', 33.5714, -117.7263, 'FREE_EMPANADAS', 'hash_javiers_01'),
('v2_arcade', 'Neon Quarter Arcade Bar', 33.5750, -117.7210, 'BOGO_TOKENS', 'hash_arcade_02');

-- Injecting the Test Subjects (The Vibe Pool)
-- User A: The Aesthete (High compatibility for deep cuts, low dominance)
INSERT INTO users (id, email, hashed_password, base_name) VALUES 
('usr_alpha', 'test1@vibe.local', 'mock_hash', 'Cassian');
INSERT INTO vibe_vectors (user_id, spotify_valence, spotify_danceability, twitter_dominance, humor_darkness) VALUES 
('usr_alpha', 0.200, 0.350, 0.850, 0.900);

-- User B: The Toxic Variable (Destined for the Shadowban pool)
INSERT INTO users (id, email, hashed_password, base_name) VALUES 
('usr_beta', 'test2@vibe.local', 'mock_hash', 'Marcus');
INSERT INTO vibe_vectors (user_id, spotify_valence, spotify_danceability, twitter_dominance, humor_darkness) VALUES 
('usr_beta', 0.900, 0.800, 0.100, 0.200);

-- Pre-loading Karma to demonstrate the hierarchy
INSERT INTO karma_ledger (user_id, event_type, karma_delta) VALUES
('usr_alpha', 'ACCOUNT_CREATION', 10),
('usr_beta', 'GHOSTED_BETA_TEST', -50); 
-- Marcus is already dying in the algorithm.