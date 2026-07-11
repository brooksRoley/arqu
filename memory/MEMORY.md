# ChannelZero — Project Memory

## Product Thesis
**Source of truth for product direction: CLAUDE.md's Creative Direction section.**

ChannelZero is a suite of immersive self-expression and hypnosis experiences with an embedded psychoanalysis layer. Priority order:
1. **Self-expression** — journal (text/draw/audio), glass video studio, speed reader, check-in.
2. **Hypnosis / entrainment** — binaural & trance audio, spiral, star-tunnel breath journey, generative visuals (Tone.js + Web Audio + Canvas).
3. **Routine / ritual building** — daily loops the user returns to.
4. **Embedded gaming** — small introspective games/rituals.
5. **Psychoanalysis insights from OAuth connections** — per-connector LLM narratives over the user's OWN data (Spotify→sonic psyche, GitHub→maker's mind, etc.). Runs on user-supplied LLM keys, needs no embeddings and no Pinecone.

**SHELVED (do not build on without explicit ask):** The Pinecone vibe-vector matching network (ANN "three shadows", mutual-match swiping, karma ledger). The OpenAI embed key is intentionally unfunded — `/api/health/embeddings` returns 429 and Pinecone is empty. Matching code degrades gracefully and stays dormant. Grow OAuth insights instead.

## OAuth Connectors (sources of psychoanalysis narrative, not matching signals)

| Provider | Status | Narrative Frame |
|----------|--------|-----------------|
| Spotify | Live | Sonic psyche — genre, mood, listening patterns |
| X (Twitter) | Live | Neurotic output — public signal analysis |
| Strava | Live | Somatic ledger — body as behavior |
| Google Calendar | Live | Temporal anxiety — time as identity |
| GitHub | Live | Maker's mind — builder intensity + repo audit |
| YouTube | Live | Parasocial field — attention + parasocial investment |
| Reddit | Live | Tribal signal — community + behavioral profile |
| Steam | Backend built, frontend card exists | Isolation metric — game library |
| Letterboxd | Backend built, frontend card exists | Empathy simulator — film taste |
| Co-Star | Backend built, frontend card exists | Fatalism mirror — astrology |
| Instagram | Backend built | Aesthetic mirror |
| TikTok | Backend built | Cultural velocity |

## Key Architectural Decisions

- **Auth**: JWT HS256, 24hr expiry, stored as `channelzero-jwt` in localStorage
- **Physics**: Matter.js bundled via npm (was CDN, migrated 2026-04-20), Canvas 2D rendering (not Three.js/WebGL)
- **Encryption**: AES-256-GCM for all stored OAuth tokens and confessional text
- **Vectors**: Pinecone serverless (AWS us-east-1), cosine similarity, 1536-dim via OpenAI text-embedding-3-small
- **Namespaces**: `users` (psychological coordinates), `journal` (RAG entries), `images` (brain image library)
- **Frontend deploy**: Vercel auto-deploy from main, TypeScript CI gate (vue-tsc --noEmit)
- **Backend deploy**: Render, uvicorn, auto-deploy from main, migrations auto-run at start
- **Analytics**: Session events, funnel steps, home streak instrumented in `useAnalytics.ts` (shipped 2026-06-21)

## Tried and Abandoned

- **CDN-loaded Matter.js**: Replaced with npm bundle 2026-04-20 — CDN failure risked taking down all physics views
- **Direct CLIP embedding for brain images**: Rejected — requires torch/transformers as dependency, too heavy. Using GPT-4o vision → text-embedding-3-small instead (same 1536-dim index)

## Open Decisions

- **Spotify audio features deprecation**: Fallback added 2026-04-20 (genre-to-valence mapping + track popularity as energy proxy). Needs monitoring.
- **OpenAI embed key**: Still broken as of 2026-07-08 — `/api/health/embeddings` returns 429 `insufficient_quota` (was 403 as of 2026-04-20, project `proj_8pERhmljbOUkRzurStcMGtZ5`). Pinecone reachable but empty (0 vectors). Pipeline now formally shelved behind `ENABLE_EMBEDDINGS` flag (default false) per CLAUDE.md Creative Direction — key is intentionally unfunded; re-fund only if matching is ever revived.

## Changelog

### 2026-07-08
- Keep-warm GitHub Actions cron added (`.github/workflows/keep-warm.yml`, GET /health every 10 min) — Render free-plan cold starts were breaking OAuth callbacks
- Embedding pipeline formally shelved: `ENABLE_EMBEDDINGS` flag (default false) gates boot probe (`main.py`) and all vector service entry points (`vector/service.py`)
- GameView + UniverseView: "Matching is coming soon — connect more data to unlock" placeholder when no match results (replaces silent no-op / fake failure)
- Star.vue rewritten as valid SFC with npm `import * as Tone from 'tone'` (was an inert snippet assuming a never-loaded CDN global; no CDN tag existed in index.html)
- Embed key audit: 429 insufficient_quota confirmed, Pinecone empty

### 2026-06-29
- Rewrote memory files to match CLAUDE.md Creative Direction pivot (self-expression first, matching shelved)
- Re-routed post-onboarding destination from `/game` to `/journal` in DiscoveryView.vue, OnboardingView.vue, SideBar.vue

### 2026-06-21
- Instrumented self-expression core loop: session events, funnel steps, home streak in `useAnalytics.ts`, `HomeView.vue`, `JournalView.vue`, `CheckInView.vue`, `ZeromindView.vue`

### 2026-05-26
- Fixed Oracle synthesis: frontend now sends all 12 providers (was only 7, missing github/youtube/reddit/instagram/tiktok)
- Migration automation: added `python -m app.migrate` to Render start command (was build-only)
- Verified TypeScript CI gate already active in vercel.json
- Verified psychometrics scoring is real (not stubbed) — IPIP-NEO + ECR-R have full implementations
- Memory files updated to reflect current state

### 2026-05-09 to 2026-05-18
- YouTube connector: OAuth flow, data fetch, attention profile, psychoanalysis endpoint — all complete
- Norm scoring (`a26423d`): Real IPIP-NEO + ECR-R scoring replaces stubs
- Radar canvas (`966a703`): RadarCanvas component in PsychoanalysisView for psychometric visualization
- Prompts audit (`290e429`)

### 2026-04-21
- Oracle synthesis auto-triggers on 2nd provider connect (real data, not flags)
- PsychCoordinate persisted to DB (`vibe_vectors.oracle_coordinate`)
- Cross-provider match scoring: Twitter/Strava/Oracle overlap in match response
- Universe + Game views surface Oracle metrics and cross-provider signals
- Admin insights: archetype distribution, attachment styles, connector depth histogram
- Zeromind trance sessions stored in `vibe_vectors.zeromind_data` and folded into matching

### 2026-04-20
- Matter.js migrated from CDN to npm
- Spotify audio features fallback added
- Brain image library backend built (upload → GPT-4o → embed → Pinecone traverse)

### 2026-04-08
- Sidebar, universe page, login UX, game reframe, calibrate cleanup
