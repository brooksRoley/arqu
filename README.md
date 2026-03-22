# Channel Zero

> "Since you have already decided to surrender your surface, we will map your depths."

Psychoanalytic profiling engine disguised as a meditation app. Your listening history, your journal, your confessions are reduced to a single coordinate point in a 1,536-dimensional psychological space. Three shadows served per night. You either show up or you don't.

## The Pipeline

```
Login → Poll (profiling) → Journal → Intake (confessional) → Game (deployment)
```

- **Poll** — Dissociation/fantasy quiz derives attachment archetype + theme palette
- **Journal** — Write, draw, record audio. Local-first with backend sync (entries auto-embed into Pinecone)
- **Check-In** — Daily dashboard: mood arc, streak, synthesis, intention setting
- **Intake** — Psychoanalytic confessional. Text encrypted at rest (AES-256-GCM). NLP extracts attachment style + defense mechanism. Confession + Spotify profile → 1,536-dim embedding → user's coordinate in Pinecone
- **Game** — ANN query on Pinecone returns 3 nearest psychological neighbors. Karma mechanics shift coordinates over time

## Experiences

Binaural entrainment, visual sync, and trance induction modules:

- **Star Tunnel** (`/webaudio`) — Starfield with binaural beat layers
- **Zeromind** (`/zeromind`) — Generative visuals + streaming text
- **Spiral** (`/spiral`) — Hypnotic spiral with trance words
- **Tone Engine** (`/trance`) — Raw binaural tone laboratory (theta/delta descent)

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | Vue 3 + Vite + TypeScript |
| Backend | FastAPI + asyncpg (Python) |
| Primary DB | Neon (serverless PostgreSQL) |
| Vector DB | Pinecone (ANN matching + semantic memory) |
| Embeddings | OpenAI `text-embedding-3-small` (1,536 dims, server-level key) |
| Encryption | AES-256-GCM (confession logs, API keys, OAuth tokens) |
| Auth | JWT (24-hour tokens, Argon2 password hashing) |
| Deployment | Vercel (frontend) + Render (backend) |

---

## Architecture

### The Two-Database Split

**Neon handles the rigid rules of the physical world.**
Users, journal entries, poll results, karma events, venues, OAuth tokens — anything with a foreign key or a timestamp lives here.

**Pinecone maps the fluid landscape of the mind.**
One vector per user (`users` namespace). One vector per journal entry (`journal` namespace). Single index at 1,536 dims (cosine). ANN queries return the 3 people physically closest in psychological space in milliseconds, regardless of user count.

### Vibe Vector Generation

```
Intake confession text
  + Spotify: top artists, genres, valence, danceability, energy
  → OpenAI text-embedding-3-small
  → 1,536-dim float array
  → Pinecone "users" namespace  (ID = user UUID)
```

The coordinate is re-plotted on every intake session and every Spotify reconnect.

### Karma Penalty

When karma drops, the vector is perturbed with Gaussian noise (σ scaled to penalty magnitude). The coordinate drifts away from healthy clusters into the margins where it only bumps into other anomalies.

```python
await apply_karma_penalty(user_id, karma_delta=-30)  # σ = 0.30
```

### Journal Semantic Memory

Journal entries embed into Pinecone's `journal` namespace on create/sync (fire-and-forget). During intake, the server queries for the 5 most semantically resonant past entries and returns them as `memories[]`. Readiness score nudges +3 per memory hit.

---

## API Routes

| Method | Path | Description |
|---|---|---|
| POST | `/api/auth/register` | Create account |
| POST | `/api/auth/login` | Get JWT |
| GET | `/api/auth/me` | Current user |
| POST | `/api/journal/entries` | Create entry (auto-embeds to Pinecone) |
| GET | `/api/journal/entries` | List entries |
| PATCH | `/api/journal/entries/:id` | Update entry |
| POST | `/api/journal/sync` | Offline-first bulk sync |
| POST | `/api/poll/submit` | Submit personality quiz |
| POST | `/api/intake/confess` | Confessional → vibe vector → Pinecone |
| GET | `/api/intake/vector` | Current vibe vector (Neon) |
| GET | `/api/intake/match` | 3 nearest psychological neighbors (Pinecone ANN) |
| GET | `/api/spotify/connect` | Redirect to Spotify OAuth |
| GET | `/api/spotify/callback` | OAuth callback — fetches audio profile, re-embeds |
| POST | `/api/llm/proxy` | Forward LLM request with user's stored key |
| POST | `/api/llm/keys` | Store encrypted LLM API key |

---

## Database Migrations

Migrations run in order on deploy (`python -m app.migrate`):

| File | Contents |
|---|---|
| `001_init.sql` | users, journal_entries, poll_tokens, audio_clips, user_api_keys |
| `002_intake.sql` | intake_shadow_logs, vibe_vectors |
| `003_social.sql` | oauth_tokens, karma_ledger, venues, `vibe_vectors.spotify_data` |

---

## Setup

```sh
cp .env.example .env   # fill in keys — see Environment section
npm install
npm run dev
```

### Backend

```sh
cd server
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m app.migrate
uvicorn app.main:app --reload
```

---

## Environment Variables

```bash
# Neon (PostgreSQL)
DATABASE_URL=
DATABASE_URL_UNPOOLED=

# Auth
JWT_SECRET=              # generate: openssl rand -hex 32
SERVER_ENCRYPTION_KEY=   # generate: openssl rand -hex 32  (rotating breaks encrypted rows)

# Pinecone
PINECONE_API_KEY=
PINECONE_INDEX=channelzero

# Embeddings (server-level key — NOT stored per user)
OPENAI_EMBED_KEY=        # used only for vibe vectors + journal embeddings

# Spotify OAuth
SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=
SPOTIFY_REDIRECT_URI=https://your-api.render.com/api/spotify/callback

# CORS + Frontend
CORS_ORIGINS=http://localhost:5173,https://channelzero.vercel.app
VITE_API_URL=http://localhost:8000
```

---

## Deploy

- **Frontend** — Vercel (auto-deploys from main)
- **Backend** — Render (blueprint in `render.yaml`, auto-migrates on build)

---

## TODO

### Spotify (next up)
- [ ] Wire `src/views/OauthView.vue` into the router at `/calibrate`
- [ ] Convert `src/composables/useVibeStore.js` to TypeScript; call `GET /api/spotify/connect` from `processOAuthCallback`
- [ ] Handle Spotify token refresh — access tokens expire in 1 hour; add silent refresh on 401 from Spotify API
- [ ] Show Spotify connection status in nav / profile

### Match Presentation
- [ ] Nightly match batch — pre-compute 3 matches per user at 3 AM (cron), cache in a `daily_matches` table with `expires_at = midnight`
- [ ] Replace live `GET /intake/match` ANN query with pre-computed batch read (required for scale beyond ~10k users)
- [ ] Radar chart — port `get_matches.py`'s 4-axis spider chart to a Canvas/SVG Vue component; overlay the two users' vibe profiles (valence, danceability, neuroticism, humor darkness)
- [ ] Match countdown timer — frontend shows time until tonight's shadows expire

### Karma Ledger
- [ ] `POST /api/karma/event` — record `POS_HANDSHAKE`, `GHOSTED`, `CO_OP_MODE` events
- [ ] `GET /api/karma/score` — rolling SUM from karma_ledger
- [ ] Wire `apply_karma_penalty()` to score drops (already implemented in `vector/service.py`)
- [ ] POS handshake: QR scan at partnered venue → verify `qr_seed` → fire event + push notification
- [ ] Seed venues table with real partners

### Twitter / X
- [ ] `server/app/twitter/` — OAuth 2.0 flow (same pattern as Spotify)
- [ ] Fetch followed accounts, liked tweets, posting patterns
- [ ] Extract `humor_darkness` + `dominance` scores via LLM from tweet corpus
- [ ] Blend Twitter linguistic profile into vibe vector embedding text

### Google Calendar
- [ ] `server/app/gcal/` — OAuth 2.0 + Calendar API
- [ ] Extract availability matrix (free blocks, recurring commitments)
- [ ] Cross-reference matched users' calendars for shared windows
- [ ] Query local event APIs → generate single curated itinerary

### Co-op Mode
- [ ] Post-date rating prompt for both users
- [ ] Romantic miss → slide to platonic pool + `CO_OP_MODE` karma event
- [ ] Community tier unlock on successful platonic conversion

### LLM-Powered Intake
- [ ] Replace `_analyze_local()` keyword NLP with a real LLM call via the proxy
- [ ] Use Pinecone-retrieved memories as context in the system prompt
- [ ] Return richer insight with specific journal callbacks
