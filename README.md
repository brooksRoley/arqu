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

### Security Audit Findings (2026-03-22)

Red-team audit identified 15 vulnerabilities. Critical and high items remediated in-tree; remaining items below.

#### Remediated (in current codebase)

- [x] **CRIT 1.1** — `config.py` had insecure defaults for `jwt_secret` / `server_encryption_key`. Fixed: removed defaults, app crashes on boot if unset.
- [x] **CRIT 2.1** — Oracle prompt injection. Raw user JSON dumped into LLM system prompt via f-string with no delimiters. Fixed: XML `<user_data>` / `<provider>` tags, anti-injection directive, `_sanitize_provider()` 50KB cap.
- [x] **HIGH 2.3** — `ProviderPayload.data` accepted arbitrary dicts with no size limit. Fixed: Pydantic `field_validator` rejects payloads > 50KB.
- [x] **MED 2.4** — LLM proxy forwarded arbitrary `max_tokens` / `messages` / `provider`. Fixed: 4096 token ceiling, provider allowlist, 100-message cap.
- [x] **CRIT 3.2** — Karma ledger had no dedup protection. Fixed: `idempotency_key UNIQUE` column in migration 004.
- [x] **HIGH 3.3** — `apply_karma_penalty()` had a read-modify-write race on Pinecone vectors. Fixed: per-user `asyncio.Lock`, zero-norm guard.
- [x] **HIGH 3.4** — Intake shadow log + vibe vector upsert used separate connections (non-atomic). Fixed: single `get_tx()` transaction.
- [x] **MED 3.5** — `ConfessRequest.confessions` had no bounds. Fixed: 1–20 items, 5000 chars each.
- [x] **HIGH 4.1** — Spotify OAuth state JWT was replayable within 10-min TTL. Fixed: nonce in JWT + `_oauth_nonces` table with UNIQUE constraint, consumed on first use.

#### Open — Secrets & Credentials

- [ ] **Rotate Render/Vercel env vars** — While `.env` was never committed to git and secrets are not in history, the local `.env` contains live production keys. If this file was ever shared, backed up to iCloud, or copied to a staging box, those keys are compromised. Rotation is cheap insurance: regenerate `JWT_SECRET`, `SERVER_ENCRYPTION_KEY`, `PINECONE_API_KEY`, `OPENAI_EMBED_KEY`, `SPOTIFY_CLIENT_SECRET`, and `PGPASSWORD` in your deployment platform. **Note:** rotating `SERVER_ENCRYPTION_KEY` breaks all encrypted rows (oauth_tokens, shadow_logs, user_api_keys) — you'll need a migration that re-encrypts with the new key or wipes and re-auths.
- [ ] **Add pre-commit hook** — `git-secrets` or Husky hook to scan for `sk-proj-*`, `pcsk_*`, connection strings before commit.

#### Open — Auth Hardening

- [ ] **MED 4.2** — Spotify `/connect` accepts JWT as `?token=` query param (exposed in browser history, server logs, Referer headers). Ideal fix: short-lived HTTP-only cookie for OAuth initiation, or a backend-generated one-time redirect token.
- [ ] Rate-limit `/api/auth/login` and `/api/auth/register` (brute-force / credential-stuffing protection).
- [ ] Extend OAuth nonce pattern to Twitter, Google, Strava, Letterboxd, Steam callback handlers.

#### Open — Testing (Coverage: 0%)

- [ ] **CRIT 3.1** — Zero test files exist across entire codebase (frontend and backend).
- [ ] Add `pytest` + `pytest-asyncio` + `httpx` test suite for backend. Priority targets:
  - [ ] `vector/service.py` — `upsert_user_vector`, `find_nearest_users`, `apply_karma_penalty` (concurrent penalty test)
  - [ ] `intake/router.py` — `/confess` (empty array, oversized payload, concurrent requests), `/match`
  - [ ] `oracle/service.py` — prompt injection payloads, malformed LLM response, timeout handling
  - [ ] `spotify/router.py` — state replay, expired state, concurrent callbacks
- [ ] Add `vitest` + `@vue/test-utils` for frontend. Priority targets:
  - [ ] `useVibeStore` — `markConnected` races, `triggerSynthesis` payload shape, `disconnectAll` idempotency
  - [ ] OAuth connect components — callback handling, error states
- [ ] Database constraint tests — `CHECK` constraints for `readiness_score` (0–100), `attachment_style` / `defense_mechanism` ENUMs, `event_type` validation on `karma_ledger`

#### Open — Schema Hardening

- [ ] **LOW 4.3** — `seed.sql` uses wrong column names (`hashed_password` vs `password_hash`, `gps_long` vs `gps_lng`). Fix or delete seed file.
- [ ] Add `CHECK` constraints: `readiness_score BETWEEN 0 AND 100`, `karma_delta` range bounds
- [ ] Add `provider CHECK IN (...)` on `oauth_tokens` table
- [ ] Migration runner (`migrate.py`) should wrap each migration in a transaction

### BYOK LLM Architecture (User-Supplied API Keys)

> **Goal:** Users bring their own LLM API keys so Oracle synthesis, intake analysis, and community games run on *their* tokens instead of our server-level `OPENAI_EMBED_KEY`.

- [ ] Add OAuth/BYOK flows for: **OpenAI**, **Anthropic (Claude)**, **Google (Gemini)**, **xAI (Grok)**
- [ ] Extend `user_api_keys` table — already supports `provider` field (`'anthropic'`, `'openai'`, `'together'`); add `'google'`, `'xai'`
- [ ] Extend `/api/llm/proxy` to support Gemini (`generativelanguage.googleapis.com`) and Grok (`api.x.ai`) endpoints
- [ ] **Oracle synthesis provider selection** — if user has a stored key, use it instead of the server key. Fallback chain: user's preferred provider → server `OPENAI_EMBED_KEY` → error
- [ ] **Embeddings stay server-side** — `text-embedding-3-small` calls must use the server key (all users must embed into the same vector space for ANN matching to work). BYOK applies only to chat/synthesis calls.
- [ ] Frontend: add provider selector + key input to `/calibrate` or a new `/settings` page. Reuse the `StoreKeyRequest` / encrypted storage pattern from `llm/router.py`.
- [ ] Community game prompts (Co-Star oracle, async psychoanalysis) should route through user's stored key when available

### Peripheral Sync Backend

- [ ] `server/app/strava/` — OAuth 2.0 (`activity:read_all` scope), fetch activities, calculate exertion/masochism metric
- [ ] `server/app/costar/` — Headless scraper microservice (Playwright), credential proxy, chart extraction
- [ ] `server/app/letterboxd/` — OAuth 2.0 (enterprise API), diary/watchlist ingestion, pretension scoring
- [ ] `server/app/steam/` — OpenID 2.0 verification, Steam Web API for recent games, isolation metric

### Match Presentation

- [ ] Nightly match batch — pre-compute 3 matches per user at 3 AM (cron), cache in a `daily_matches` table with `expires_at = midnight`
- [ ] Replace live `GET /intake/match` ANN query with pre-computed batch read (required for scale beyond ~10k users)
- [ ] Radar chart — port `get_matches.py`'s 4-axis spider chart to a Canvas/SVG Vue component; overlay the two users' vibe profiles (valence, danceability, neuroticism, humor darkness)
- [ ] Match countdown timer — frontend shows time until tonight's shadows expire

### Karma Ledger

- [ ] `POST /api/karma/event` — record `POS_HANDSHAKE`, `GHOSTED`, `CO_OP_MODE` events (use `idempotency_key` to prevent duplicate handshakes)
- [ ] `GET /api/karma/score` — rolling SUM from karma_ledger
- [ ] Wire `apply_karma_penalty()` to score drops (already implemented in `vector/service.py`)
- [ ] POS handshake: QR scan at partnered venue → verify `qr_seed` → fire event + push notification
- [ ] Seed venues table with real partners

### Co-op Mode

- [ ] Post-date rating prompt for both users
- [ ] Romantic miss → slide to platonic pool + `CO_OP_MODE` karma event
- [ ] Community tier unlock on successful platonic conversion

### LLM-Powered Intake

- [ ] Replace `_analyze_local()` keyword NLP with a real LLM call via the proxy (use user's BYOK key if available)
- [ ] Use Pinecone-retrieved memories as context in the system prompt
- [ ] Return richer insight with specific journal callbacks
