# ChannelZero — Claude Code Guide

## Stack
- **Frontend**: Vue 3 + Vite + TypeScript + Tailwind — deployed to Vercel (`channelzero.vercel.app`)
- **Backend**: FastAPI (Python) — deployed to Render (`channelzero-api.onrender.com`)
- **Database**: Neon PostgreSQL (asyncpg pooled + unpooled connections)
- **Vector DB**: Pinecone (`channelzero` index) — vibe vectors for user matching
- **Auth**: JWT HS256, 24hr expiry, stored as `channelzero-jwt` in localStorage

## Project Structure
```
/src
  /views          — Route-level page components
  /components     — Reusable UI components
  /composables    — Business logic and state (useAuthStore, useVibeStore, etc.)
  /router         — index.ts with auth guard
/server
  /app
    /auth         — Login, register, JWT, Google/X OAuth identity
    /analytics    — Admin funnel + connector metrics + insights panels
    /brain        — Image library (upload, browse, embeddings, similarity)
    /costar       — Co-Star credential-based natal chart ingestion
    /gcal         — Google Calendar OAuth + temporal pattern extraction
    /intake       — Psychoanalytic confessional pipeline + matching
    /journal      — Journal CRUD + vector embeddings
    /letterboxd   — Letterboxd API film taste ingestion
    /llm          — Encryption helpers (AES-256-GCM)
    /match        — Accept/reject interactions + mutual match detection
    /messages     — Encrypted mutual-match messaging
    /oracle       — 7D psychological synthesis + Pinecone upsert
    /poll         — Archetype poll tokens
    /psychometrics — Multi-part assessment scoring + profile generation
    /spotify      — Spotify OAuth + sonic profile
    /steam        — Steam OpenID + game library ingestion
    /strava       — Strava OAuth + activity data
    /twitter      — X OAuth 2.0 PKCE data connector
    /vector       — Pinecone upsert/query + zeromind sessions
  /migrations     — SQL files run by migrate.py (tracked in _migrations table)
```

## Auth Patterns
- `useAuthStore` — exposes `token`, `user`, `apiFetch` (auto-attaches Bearer token)
- Backend: `get_current_user_id` dep → returns UUID; `require_admin` dep → checks `is_admin` column
- Protected routes: `meta: { requiresAuth: true }` in router; guest-only: `meta: { guest: true }`
- Admin access: set `is_admin = true` in `users` table directly via Neon

## Database Conventions
- Migrations live in `server/migrations/NNN_name.sql`
- Run locally: `source server/venv/bin/activate && python -m server.app.migrate`
- Connections: use pooled `DATABASE_URL` for app, unpooled `DATABASE_URL_UNPOOLED` for migrations and admin queries
- OAuth tokens encrypted with AES-256-GCM via `encrypt_api_key` / `decrypt_api_key`

## Key Composables
| Composable | Purpose |
|---|---|
| `useAuthStore` | JWT token, user object, `apiFetch` wrapper |
| `useVibeStore` | Intake/vibe vector state, OAuth connection state |
| `useCosmicPhysics` | Matter.js physics: orbs, particles, stars, spring attractors |
| `useSpotifyPhysics` | Wraps cosmic physics with Spotify audio data (genre→color, valence field) |
| `useAdminStore` | Admin analytics API calls (funnel, connectors, users, events) |
| `useMessageStore` | Real-time messaging between matched users |

## Canvas / Physics Pattern
- `useCosmicPhysics(canvasRef, options)` — base physics engine (Matter.js via CDN)
- Two-canvas pattern: base canvas (physics) + overlay canvas (labels, HUD)
- `getOrbPositions()` returns current `{x, y, idx}[]` for overlay label placement
- Custom `rrect()` helper for rounded rects (avoids TypeScript `ctx.roundRect` compat issues)

## Deploy Workflow
1. `npm run build` locally to verify no TypeScript errors (`vue-tsc --noEmit`)
2. `git push origin main` → Vercel auto-deploys frontend
3. Render auto-deploys backend on push (build dir: `server/`, start: `uvicorn server.app.main:app`)
4. After new migrations: manually trigger `python -m server.app.migrate` or add to Render build command

## Env Vars (Render must have all of these)
`DATABASE_URL`, `DATABASE_URL_UNPOOLED`, `JWT_SECRET`, `SERVER_ENCRYPTION_KEY`,
`PINECONE_API_KEY`, `OPENAI_EMBED_KEY`,
`SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, `SPOTIFY_REDIRECT_URI`,
`X_CLIENT_ID`, `X_CLIENT_SECRET`, `TWITTER_DATA_REDIRECT_URI`,
`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`,
`STRAVA_CLIENT_ID`, `STRAVA_CLIENT_SECRET`,
`GCAL_REDIRECT_URI`,
`STEAM_API_KEY`,
`LETTERBOXD_API_KEY`, `LETTERBOXD_API_SECRET`,
`CORS_ORIGINS`

## Commit Style
- Short, imperative subject line — no body needed for small changes
- No `Co-Authored-By` lines
- Prefer one focused commit per feature/fix

## Route Map
| Route | Auth | Purpose |
|---|---|---|
| `/` | no | Home hub |
| `/login` | guest | Auth |
| `/learn` | no | Learn index |
| `/learn/:slug` | no | Learn article |
| `/sessions` | no | Sessions listing |
| `/about` | no | About page |
| `/discovery` | yes | Physics-driven onboarding |
| `/onboarding` | yes | Onboarding flow |
| `/calibrate` | yes | All connector OAuth (Spotify, X, Strava, CoStar, Letterboxd, Steam) |
| `/intake` | yes | Psychometric confessional intake |
| `/psychoanalysis` | yes | Psychometric assessment + narrative |
| `/game` | yes | Oracle matching game |
| `/universe` | yes | Solar system signal visualization |
| `/spotify` | yes | Spotify sonic field physics |
| `/x` | yes | X/Twitter signal visualization |
| `/messages` | yes | Mutual match messaging |
| `/messages/:userId` | yes | Thread view |
| `/journal` | yes | Journal editor (text, drawing, audio, mood) |
| `/checkin` | yes | Daily check-in + mood arc |
| `/admin` | yes+admin | Analytics dashboard |
| `/zeromind` | no | Trance entrainment (Tone.js) |
| `/audio` | no | Adaptive entrainment audio player |
| `/trance` | no | Trance visualization |
| `/hypno` | no | Hypno visualization |
| `/spiral` | no | Spiral visualization |
| `/studio` | no | Glass studio |
| `/liquidglass` | no | Liquid glass experiment |
| `/fitting` | no | Body/swimsuit configurator (standalone) |
| `/fitting/:matchId` | yes | Pre-reveal avatar ritual (self + ideal) |
| `/reveal/:matchId` | yes | Match reveal scroll narrative |
| `/poll` | no | Archetype poll |
| `/reader` | no | Reader view |
| `/webaudio` | no | WebAudio experiment |
