# ChannelZero — Project Memory

## Product Thesis
ChannelZero matches people through behavioral signals, not profile browsing. Users connect data providers (Spotify, X, Strava, etc.) and complete psychometric intake. The Oracle synthesizes 7 provider streams into a psychological coordinate vector. Pinecone ANN finds the nearest neighbors in that space — your matches are the people whose behavioral fingerprints are closest to yours.

## Active Connectors

| Provider | Status | Data Used |
|----------|--------|-----------|
| Spotify | Live | Top artists, genres, audio features (with genre-based fallback for deprecation) |
| X (Twitter) | Live | OAuth 2.0 PKCE, tweet analysis for "neurotic output" signal |
| Strava | Live | Activity data as "somatic ledger" signal |
| Google Calendar | Live (OAuth) | Temporal patterns as "temporal anxiety" signal |
| Steam | Backend built, frontend card exists | Game library as "isolation metric" |
| Letterboxd | Backend built, frontend card exists | Film taste as "empathy simulator" |
| Co-Star | Backend built, frontend card exists | Astrology data as "fatalism mirror" |

## Key Architectural Decisions

- **Auth**: JWT HS256, 24hr expiry, stored as `channelzero-jwt` in localStorage
- **Physics**: Matter.js bundled via npm (was CDN, migrated 2026-04-20), Canvas 2D rendering (not Three.js/WebGL)
- **Encryption**: AES-256-GCM for all stored OAuth tokens and confessional text
- **Vectors**: Pinecone serverless (AWS us-east-1), cosine similarity, 1536-dim via OpenAI text-embedding-3-small
- **Namespaces**: `users` (psychological coordinates), `journal` (RAG entries), `images` (brain image library)
- **Frontend deploy**: Vercel auto-deploy from main
- **Backend deploy**: Render, uvicorn, auto-deploy from main
- **Match delivery**: Toast notification component polls `/api/match/new` every 30s, marks seen via `/api/match/seen`
- **Oracle auto-trigger**: Fires when user connects 2nd+ provider, uses real JSONB from vibe_vectors

## Tried and Abandoned

- **CDN-loaded Matter.js**: Replaced with npm bundle 2026-04-20 — CDN failure risked taking down all physics views
- **Direct CLIP embedding for brain images**: Rejected — requires torch/transformers as dependency, too heavy. Using GPT-4o vision → text-embedding-3-small instead (same 1536-dim index)

## Open Decisions

- **Spotify audio features deprecation**: Fallback added 2026-04-20 (genre-to-valence mapping + track popularity as energy proxy). Needs monitoring — if Spotify fully removes the endpoint, the fallback activates automatically.
- **Migration automation**: Migrations are manual (`python -m server.app.migrate`). No CI step runs them automatically on deploy.
- **OpenAI API key**: Project `proj_8pERhmljbOUkRzurStcMGtZ5` was returning 403 as of 2026-04-20. All vector operations depend on this key.
- **Psychometrics scoring stubbed**: IPIP-NEO and ECR-R in `scoring.py` return placeholder values — real scoring not implemented.

## Changelog

### 2026-04-21
- Oracle synthesis auto-triggers on 2nd provider connect (real data, not flags)
- PsychCoordinate persisted to DB (`vibe_vectors.oracle_coordinate`)
- Cross-provider match scoring: Twitter/Strava/Oracle overlap in match response
- Universe + Game views surface Oracle metrics and cross-provider signals
- Admin insights: archetype distribution, attachment styles, connector depth histogram
- Zeromind trance sessions stored in `vibe_vectors.zeromind_data` and folded into matching
- All 6 connector cards confirmed live in OauthView (Spotify, X, Strava, CoStar, Letterboxd, Steam)

### 2026-04-20
- Matter.js migrated from CDN to npm
- Spotify audio features fallback added
- Brain image library backend built (upload → GPT-4o → embed → Pinecone traverse)

### 2026-04-08
- Sidebar, universe page, login UX, game reframe, calibrate cleanup
