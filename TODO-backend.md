# ChannelZero Backend — Implementation Plan

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│  Vercel (Free Tier)                                 │
│  ┌───────────────┐   ┌──────────────────────────┐   │
│  │ Vue 3 SPA     │   │ Vercel Postgres (Neon)   │   │
│  │ (frontend)    │   │ - users table            │   │
│  │ channelzero.  │   │ - journal_entries        │   │
│  │ vercel.app    │   │ - poll_tokens            │   │
│  └───────┬───────┘   │ - encrypted_api_keys     │   │
│          │           └──────────┬───────────────┘   │
│          │                      │                    │
└──────────┼──────────────────────┼────────────────────┘
           │                      │
           ▼                      ▼
┌─────────────────────────────────────────────────────┐
│  Render.io (Free Tier)                              │
│  ┌───────────────────────────────────────────────┐  │
│  │ FastAPI Service                               │  │
│  │ - /api/auth/*        (login, register, me)    │  │
│  │ - /api/journal/*     (CRUD, sync, synthesis)  │  │
│  │ - /api/llm/proxy     (user's own key, e2e)    │  │
│  │ - /api/poll/*        (save/load poll tokens)  │  │
│  └───────────────────────────────────────────────┘  │
│  ~512MB RAM, sleeps after 15min idle                │
│  Auto-deploy from GitHub branch                     │
└─────────────────────────────────────────────────────┘
```

## Why This Split

- **Vercel** already hosts the frontend (or will). Vercel Postgres (powered by Neon) gives you a free PostgreSQL database — 256MB storage, plenty for journal entries and user data. Zero extra config since it's the same platform.
- **Render.io free tier** runs a single web service (FastAPI) with 512MB RAM and auto-deploy from GitHub. It sleeps after 15 min idle — fine for personal/small-user-base use. Vercel's serverless functions *could* work, but FastAPI gives you a real Python runtime for LLM proxy logic, encryption, and heavier synthesis work without cold start constraints.
- **Total cost: $0.** Both tiers are generous enough for this stage.

---

## Phase 1: Foundation (Database + Auth)

### 1.1 Vercel Postgres Setup
- [ ] Enable Vercel Postgres (Neon) in Vercel dashboard → Storage tab
- [ ] Copy `POSTGRES_URL`, `POSTGRES_PRISMA_URL`, `POSTGRES_URL_NON_POOLING` env vars
- [ ] These get passed to FastAPI via Render env vars

### 1.2 Database Schema (SQL migrations)

```sql
-- 001_init.sql
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE users (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email         TEXT UNIQUE NOT NULL,
  display_name  TEXT,
  password_hash TEXT NOT NULL,
  created_at    TIMESTAMPTZ DEFAULT now(),
  updated_at    TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE poll_tokens (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID REFERENCES users(id) ON DELETE CASCADE,
  answers     JSONB NOT NULL,
  theme       TEXT NOT NULL,
  palette     JSONB NOT NULL,
  tone        TEXT,
  archetype   TEXT,
  keywords    TEXT[],
  created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE journal_entries (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID REFERENCES users(id) ON DELETE CASCADE,
  text        TEXT DEFAULT '',
  drawings    JSONB DEFAULT '[]',      -- array of { dataUrl, createdAt }
  mood        TEXT,
  poll_token_id UUID REFERENCES poll_tokens(id),
  created_at  TIMESTAMPTZ DEFAULT now(),
  updated_at  TIMESTAMPTZ DEFAULT now()
);

-- Audio clips stored as references (actual blobs in Vercel Blob or kept client-side)
CREATE TABLE audio_clips (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  entry_id    UUID REFERENCES journal_entries(id) ON DELETE CASCADE,
  blob_url    TEXT,              -- Vercel Blob URL or null if client-only
  duration_s  REAL,
  created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE user_api_keys (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
  provider        TEXT NOT NULL,          -- 'openai', 'anthropic', 'together', etc.
  encrypted_key   BYTEA NOT NULL,         -- AES-256-GCM encrypted
  key_hint        TEXT,                   -- last 4 chars for display: '...xK4m'
  created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_journal_user ON journal_entries(user_id, created_at DESC);
CREATE INDEX idx_apikeys_user ON user_api_keys(user_id);
```

### 1.3 FastAPI Project Scaffold

```
server/
├── alembic/               # DB migrations
│   └── versions/
├── app/
│   ├── __init__.py
│   ├── main.py            # FastAPI app, CORS, lifespan
│   ├── config.py          # Settings from env vars
│   ├── db.py              # asyncpg connection pool
│   ├── auth/
│   │   ├── router.py      # POST /register, /login, /me
│   │   ├── models.py      # User pydantic models
│   │   ├── service.py     # password hashing (argon2), JWT creation
│   │   └── deps.py        # get_current_user dependency
│   ├── journal/
│   │   ├── router.py      # CRUD /journal/entries, /journal/sync
│   │   ├── models.py
│   │   └── service.py
│   ├── poll/
│   │   ├── router.py      # save/load poll tokens
│   │   └── models.py
│   ├── llm/
│   │   ├── router.py      # POST /llm/proxy (forward to user's LLM)
│   │   ├── encryption.py  # AES-256-GCM encrypt/decrypt API keys
│   │   └── service.py     # key management CRUD
│   └── middleware/
│       └── cors.py
├── requirements.txt
├── render.yaml            # Render.io deploy config
├── Dockerfile             # Optional, Render supports native Python too
└── alembic.ini
```

### 1.4 Auth Flow

```
1. User hits /journal → sees "Sign in to sync" prompt (journaling still works offline/localStorage)
2. Register: email + password → argon2 hash → DB → JWT returned
3. Login: email + password → verify → JWT (httpOnly cookie + bearer token for API)
4. JWT payload: { sub: user_id, exp: 24h }
5. Refresh: sliding window, new token on each authenticated request
6. Guest mode: everything works exactly as it does now (localStorage). Auth is additive.
```

**Key principle: Auth is opt-in.** The app works fully without an account. Signing in adds sync, cross-device persistence, and LLM features.

---

## Phase 2: Journal Sync

### 2.1 Offline-First Sync Strategy
- [ ] Journal entries always save to localStorage first (instant, no latency)
- [ ] If authenticated, queue a background sync to the API
- [ ] Sync uses `updated_at` timestamps for conflict resolution (last-write-wins)
- [ ] New composable: `useJournalSync.ts` — watches journal store, debounced POST to API
- [ ] On login, merge: pull server entries, merge with local, push local-only entries up

### 2.2 API Endpoints

```
POST   /api/journal/entries          → create entry
GET    /api/journal/entries          → list (paginated, filterable by date)
PATCH  /api/journal/entries/:id      → update text, mood, drawings
DELETE /api/journal/entries/:id      → soft delete
POST   /api/journal/sync             → bulk sync (send local state, get merged result)
GET    /api/journal/synthesis/:date  → server-side synthesis for a given day
```

---

## Phase 3: Encrypted LLM Proxy

### 3.1 How API Key Encryption Works

```
User enters their OpenAI/Anthropic/etc API key in settings
  ↓
Frontend sends key over HTTPS to:  POST /api/llm/keys
  ↓
Server encrypts with AES-256-GCM using a SERVER_ENCRYPTION_KEY (env var)
  - key_hint = last 4 chars saved in plaintext for UI display
  - encrypted_key = AES-256-GCM(plaintext_key, SERVER_ENCRYPTION_KEY, random_nonce)
  - stored in user_api_keys table
  ↓
Plaintext key NEVER stored. NEVER logged. NEVER returned in any GET response.
  ↓
When user sends a prompt:
  POST /api/llm/proxy  { provider: "anthropic", messages: [...] }
  ↓
Server decrypts key in memory → forwards request to provider API → streams response back
  ↓
Key exists in memory only during the request lifecycle. Never touches disk unencrypted.
```

### 3.2 LLM Proxy Endpoints

```
POST   /api/llm/keys           → store encrypted API key for a provider
GET    /api/llm/keys           → list providers + hints (never the actual key)
DELETE /api/llm/keys/:id       → remove a stored key
POST   /api/llm/proxy          → forward prompt to user's LLM (streaming SSE response)
```

### 3.3 Supported Providers (start small)
- Anthropic (Claude)
- OpenAI (GPT-4, etc.)
- Together AI (open models)
- Expand later as needed

---

## Phase 4: Frontend Integration

### 4.1 New Composables
- [ ] `useAuth.ts` — login, register, logout, token management, `isAuthenticated` ref
- [ ] `useJournalSync.ts` — background sync engine, conflict resolution
- [ ] `useUserLLM.ts` — manage API keys, send prompts through proxy, stream responses
- [ ] `useSettings.ts` — user preferences panel (API keys, display name, sync toggle)

### 4.2 New Components
- [ ] `AuthModal.vue` — slide-up login/register form (not a full page redirect)
- [ ] `SettingsView.vue` — API key management, account info, sync status
- [ ] `SyncIndicator.vue` — tiny status dot in NavBar (synced / syncing / offline)
- [ ] Update `JournalView.vue` — add sync status badge, "sign in to sync" prompt
- [ ] Update `CheckInView.vue` — LLM-powered synthesis when key is available

### 4.3 Router Addition
```typescript
{ path: '/settings', name: 'settings', component: () => import('@/views/SettingsView.vue') }
```

---

## Phase 5: Deploy Pipeline

### 5.1 Vercel (Frontend + DB)
- [ ] Add `vercel.json` with rewrites for SPA routing
- [ ] Enable Vercel Postgres in dashboard
- [ ] Set env vars: `VITE_API_URL` pointing to Render FastAPI service
- [ ] Auto-deploy from `main` branch

### 5.2 Render.io (FastAPI)
- [ ] Create Web Service → connect GitHub repo → point to `server/` directory
- [ ] Build command: `pip install -r requirements.txt`
- [ ] Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- [ ] Environment variables:
  - `DATABASE_URL` — Vercel Postgres connection string
  - `SERVER_ENCRYPTION_KEY` — 32-byte random key for AES-256-GCM
  - `JWT_SECRET` — separate secret for JWT signing
  - `CORS_ORIGINS` — `https://channelzero.vercel.app` (and localhost for dev)
- [ ] Add `render.yaml`:

```yaml
services:
  - type: web
    name: channelzero-api
    runtime: python
    plan: free
    buildCommand: pip install -r server/requirements.txt
    startCommand: uvicorn server.app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: DATABASE_URL
        sync: false
      - key: SERVER_ENCRYPTION_KEY
        generateValue: true
      - key: JWT_SECRET
        generateValue: true
      - key: CORS_ORIGINS
        value: https://channelzero.vercel.app
    healthCheckPath: /health
```

---

## Free Tier Limits (Reality Check)

| Service | What You Get | Enough? |
|---------|-------------|---------|
| Vercel Postgres (Neon) | 256MB storage, 1M row reads/mo | Yes — journal text is tiny |
| Vercel Bandwidth | 100GB/mo | Yes — SPA is ~400KB |
| Render Web Service | 512MB RAM, sleeps after 15min | Yes — wakes in ~30s on first request |
| Render Outbound | 100GB/mo | Yes — LLM proxy responses are text |

**When to upgrade:** If you get >50 active users or need the API to stay awake 24/7 (Render paid starts at $7/mo).

---

## Implementation Order

```
Week 1:  Phase 1 (DB schema + FastAPI scaffold + auth endpoints)
         Phase 5.1 (Vercel config + Postgres provisioning)
Week 2:  Phase 2 (journal sync — API + useJournalSync.ts)
         Phase 5.2 (Render deploy)
Week 3:  Phase 3 (encrypted API key storage + LLM proxy)
         Phase 4 (frontend integration — auth modal, settings, sync indicator)
Week 4:  Polish, edge cases, error handling, loading states
```

---

## Security Notes

- Passwords: argon2id (not bcrypt — more resistant to GPU attacks)
- API keys: AES-256-GCM with per-key random nonce, server-side encryption key from env
- JWTs: short-lived (24h), signed with separate secret
- CORS: locked to production domain + localhost
- HTTPS everywhere (Vercel and Render both enforce this on free tier)
- No API key ever returned in a GET — only hints
- Rate limiting on auth endpoints (5 attempts/min) and LLM proxy (30 req/min)
- SQL injection: impossible with parameterized queries via asyncpg
- XSS: Vue's template compiler escapes by default
