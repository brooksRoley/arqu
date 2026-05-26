---
name: ChannelZero project state
description: Current connector status, infrastructure state, known issues, and recent changes as of 2026-05-26
type: project
---

# ChannelZero — Project State

## Funnel Steps
| Step | Meaning |
|------|---------|
| registered | User created account |
| completed_poll | Took the archetype poll |
| connected_any | Connected 1+ OAuth provider |
| connected_2plus | Connected 2+ providers (triggers Oracle synthesis) |
| has_vibe_vector | Intake confession → Pinecone vector exists |
| completed_psychometrics | IPIP-NEO + ECR-R + love language assessed |
| played_game | Made at least one match interaction |
| got_mutual_match | Both sides accepted |
| sent_message | Sent a message to a mutual match |

## Connector Status (as of 2026-05-26)

| Connector | OAuth | Data Fetch | Oracle Feed | Frontend Card |
|-----------|-------|------------|-------------|---------------|
| Spotify | Live | Live (genre fallback for deprecated audio-features) | All 12 providers sent to synthesis | OauthView card + SpotifyPhysics |
| X/Twitter | Live | Live (PKCE) + LLM psychoanalysis | All 12 providers sent to synthesis | OauthView card + UniverseView |
| Strava | Live | Live (activities + stats) | All 12 providers sent to synthesis | OauthView card |
| Google Calendar | Live (OAuth) | Live (temporal patterns) | All 12 providers sent to synthesis | OauthView card (callback-based) |
| Co-Star | Backend built | Credential proxy (no OAuth) | Included if present | OauthView card (CoStarConnect) |
| Letterboxd | Backend built | API key auth + username ingest | Included if present | OauthView card (LetterboxdConnect) |
| Steam | Backend built | OpenID 2.0 + game library | Included if present | OauthView card (SteamConnect) |
| GitHub | Live (OAuth) | Developer profile + repos | Included if present | OauthView card |
| YouTube | Live (OAuth) | Subscriptions, channel stats, attention profile | Included if present | OauthView card + YouTubeCallback |
| Reddit | Live (OAuth) | Subreddit + behavioral profile | Included if present | OauthView card |
| Instagram | Backend built | Router exists | Included if present | OauthView card |
| TikTok | Backend built | Router exists | Included if present | OauthView card |

## Infrastructure

- **Pinecone**: Index `channelzero`, 3 namespaces (users, journal, images), embeddings via `text-embedding-3-small` (OPENAI_EMBED_KEY)
- **Migrations**: SQL files in `server/migrations/`, tracked in `_migrations` table, run at build AND start on Render
- **Frontend deploy**: Vercel auto-deploy from main (`channelzero.vercel.app`), TypeScript CI gate (`vue-tsc --noEmit`) in vercel.json
- **Backend deploy**: Render auto-deploy from main (`channelzero.onrender.com`)
- **Database**: Neon PostgreSQL (pooled + unpooled connections)

## Components

- **RadarCanvas** (`src/components/RadarCanvas.vue`): Canvas-based radar chart used in PsychoanalysisView to visualize psychometric scores

## Known Issues

- **Spotify audio features deprecated**: Fallback active (genre→valence mapping + track popularity as energy proxy)
- **Tone.js + Matter.js**: Matter.js on npm (migrated from CDN 2026-04-20), Tone.js still CDN — no version lock
- **OpenAI API key**: Was returning 403 as of 2026-04-20 (`proj_8pERhmljbOUkRzurStcMGtZ5`) — needs manual verification in OpenAI dashboard. Health endpoint at `/api/health/embeddings` exists for checking.

## Resolved Issues (since last update)

- **TypeScript CI**: Now active — `vue-tsc --noEmit && vite build` in both vercel.json and package.json
- **Manual migrations**: Now run automatically at Render start command (render.yaml updated 2026-05-26)
- **Psychometrics scoring**: Real scoring implemented — IPIP-NEO processes ocean_items or pre-computed scores, ECR-R has full scoring with Johnson 2014 SAPA norms and Fraley et al. (2000) norms
- **Oracle synthesis payload**: Fixed 2026-05-26 — frontend now sends all 12 providers (was only 7, missing github/youtube/reddit/instagram/tiktok)
- **YouTube in Oracle**: Confirmed wired as "Parasocial Field" in models.py, service.py, trigger.py
- **Steam card**: Restored in OauthView (was commented out)
- **GCal connected card**: Rich data display added (peak hours, overcommitment ratio bar, meeting density, avg events/week)
- **GameView keyboard**: Fixed inverted ArrowLeft/ArrowRight convention (right=accept, left=pass)
- **GameView mutual phase**: Now reachable — acceptMatch() sets phase='mutual' before routing to /fitting
- **Oracle chat loop**: Added 5th terminal response + typing indicator

## Recent Changes (2026-05-26 session)

- Fixed `triggerSynthesis()` to include all 12 providers in Oracle payload (was missing 5)
- Added migration auto-run to Render start command in render.yaml
- Verified TypeScript CI gate already in place (vercel.json + package.json)
- GCal connected card: added GCalProfile interface, fetch, watcher, rich data display
- GameView: swapped keyboard bindings (ArrowRight/Enter=accept, ArrowLeft/Escape=pass)
- GameView: mutual phase now reachable; "Begin Reveal" routes to /fitting/:matchId
- Oracle chat: added 5th terminal response, typing indicator ("...") during response delay
- Steam card restored with SteamConnect import uncommented
- Accessibility: aria-labels on star rating and feedback tag buttons
- GCal subtitle capitalized to "Time as Behavior" in both card states

## Notable Commits (2026-04-28 to 2026-05-18)

- `a26423d` Norm scoring — real IPIP-NEO + ECR-R scoring (replaces stubs)
- `966a703` Radar canvas — RadarCanvas component for psychometric visualization
- `e47d6d9` YouTube connector attempt (initial)
- `4159bd5` Fix merge conflict in youtube router
- `78afbbe` YouTube test
- `290e429` Prompts audit
- `af1ef05` ChannelZero (latest)
