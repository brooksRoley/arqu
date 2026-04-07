---

## ChannelZero Audit — 2026-04-07

---

### 1. Git Status

**Recent commits (last 15):**

| Hash | Message |
|------|---------|
| eb91017 | ZeroMind vie |
| ccdd10f | Fix dev dependencies |
| 809e3b4 | ChannelZero |
| f48119e | channel 0 homepage animations |
| 1b13860 | Foreign key build error |
| fcc18c7 | Glass component updates |
| 4a5ae63 | Query param usage |
| 824c621 | Add tone tutorial, looper studio and the query param gating |
| 79ac0b1 | AudioVisualVideo |
| 7d824b3 | Navbar update |
| 6b19c1a | Yes On strava and spotify Connects |
| b759404 | Login logout and Oauth backend work |
| 201343e | Added tests |
| a30c590 | Audit |

Recent work has been frontend-heavy: new visual experiences (ZeroMind, Glass, animations), nav, Spotify/Strava OAuth UI. One remote branch exists: `claude/add-claude-documentation-gjIcJ` (unmerged).

**Branches:** `main` (local + remote), plus `remotes/origin/claude/add-claude-documentation-gjIcJ`.

---

### 2. Frontend Tests

**Result: FAIL — test runner not installed.**

`vitest` is listed in `package.json` devDependencies (`^4.1.2`) but is not installed in `node_modules`. Running `npm run test` or `npx vitest` fails with `ERR_MODULE_NOT_FOUND`.

`pinia` is also listed as `MISSING` in npm outdated — not installed either.

**Fix required:** `npm install`

---

### 3. Python Sanity Tests

**Result: N/A — test files do not exist.**

`test_config.py` and `test_pydantic.py` were not found in `server/`. The audit note in README confirms: **0% test coverage across the entire codebase.** No `tests/` directory exists in `server/app/`.

---

### 4. Codebase Snapshot

| Directory | Files | Lines |
|-----------|-------|-------|
| `src/` | 87 | ~19,817 (TS/Vue/TSX) |
| `server/app/` | 55 | ~4,458 (Python) |

**TODO/FIXME locations:**

| File | Comment |
|------|---------|
| `server/app/letterboxd/router.py:11` | `TODO: Requires LETTERBOXD_API_KEY + LETTERBOXD_API_SECRET.` |
| `server/app/costar/router.py:11` | `TODO: Co-Star may block automated login. If their private API changes...` |

Only 2 inline TODOs — the real backlog lives in README.

---

### 5. Dependency Health

**npm outdated (critical items):**

| Package | Current | Latest | Notes |
|---------|---------|--------|-------|
| `pinia` | MISSING | 3.0.4 | **Not installed — will break at runtime** |
| `vite` | 5.2.11 | 8.0.7 | 3 major versions behind |
| `@vitejs/plugin-vue` | 5.0.4 | 6.0.5 | Major version behind |
| `vue` | 3.4.26 | 3.5.32 | Minor updates available |
| `typescript` | 5.4.5 | 6.0.2 | Major version behind |
| `@types/node` | 20.12.10 | 25.5.2 | 5 major versions behind |
| `tailwindcss` | 3.4.3 | 4.2.2 | Major version behind |
| `@vueuse/core` | 11.3.0 | 14.2.1 | 3 major versions behind |
| `eslint` | 8.57.0 | 10.2.0 | 2 major versions behind |

**Action required:** `npm install` at minimum to restore `pinia` and `vitest`. Major upgrades (Vite 8, TS 6, Tailwind 4) should be treated as separate migration tasks.

---

### 6. README TODOs

From the `## TODO` section:

**Security (Open):**
1. Rotate all production env vars (`JWT_SECRET`, `SERVER_ENCRYPTION_KEY`, `PINECONE_API_KEY`, `OPENAI_EMBED_KEY`, `SPOTIFY_CLIENT_SECRET`, `PGPASSWORD`)
2. Add pre-commit hook (`git-secrets` / Husky) to catch credential patterns before commit
3. MED 4.2: Spotify `/connect` sends JWT in `?token=` query param — switch to HTTP-only cookie or one-time redirect token
4. Rate-limit `/api/auth/login` and `/api/auth/register`
5. Extend OAuth nonce replay protection to Twitter, Google, Strava, Letterboxd, Steam

**Testing (Coverage: 0%):**
6. Add `pytest` + `pytest-asyncio` + `httpx` backend test suite — priority: `vector/service.py`, `intake/router.py`, `oracle/service.py`, `spotify/router.py`
7. Add `vitest` + `@vue/test-utils` frontend tests — priority: `useVibeStore`, OAuth connect components
8. Add database constraint tests

**Schema Hardening:**
9. Fix `seed.sql` column name mismatches (`hashed_password`, `gps_long`)
10. Add `CHECK` constraints: `readiness_score BETWEEN 0 AND 100`, `karma_delta` bounds, `provider CHECK IN (...)`
11. Wrap each migration in a transaction in `migrate.py`

**BYOK LLM (User-Supplied Keys):**
12. Add OAuth/BYOK flows for OpenAI, Anthropic, Gemini, Grok
13. Extend `/api/llm/proxy` to support Gemini + Grok endpoints
14. Oracle synthesis fallback chain: user key → server key → error
15. Frontend provider selector + key input on `/calibrate` or `/settings`

**Peripheral Sync Backend (stubs only):**
16. `strava/` — OAuth 2.0, activity fetch, exertion metric
17. `costar/` — Playwright headless scraper, credential proxy
18. `letterboxd/` — OAuth 2.0 enterprise API, diary ingestion
19. `steam/` — OpenID 2.0, Steam Web API recent games

**Match Presentation:**
20. Nightly match batch (cron) → pre-computed `daily_matches` table
21. Replace live ANN query with batch read (required at >10k users)
22. Radar chart Vue component (valence/danceability/neuroticism/humor darkness)
23. Match countdown timer on frontend

**Karma Ledger:**
24. `POST /api/karma/event` — record `POS_HANDSHAKE`, `GHOSTED`, `CO_OP_MODE`
25. `GET /api/karma/score` — rolling SUM from ledger
26. Wire `apply_karma_penalty()` to score drops
27. POS handshake via QR scan at partnered venues
28. Seed venues table

**Co-op Mode:**
29. Post-date rating prompt for both users
30. Romantic miss → slide to platonic pool + `CO_OP_MODE` karma event
31. Community tier unlock on successful platonic conversion

**LLM-Powered Intake:**
32. Replace `_analyze_local()` keyword NLP with real LLM call via proxy
33. Use Pinecone-retrieved memories as context in system prompt
34. Return richer insights with journal callbacks

---

**Immediate blockers:** Run `npm install` — `pinia` and `vitest` are missing from `node_modules`, which breaks both the app at runtime and the test suite entirely.
