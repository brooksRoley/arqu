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

## Connector Status (as of 2026-04-21)

| Connector | OAuth | Data Fetch | Oracle Feed | Frontend Card |
|-----------|-------|------------|-------------|---------------|
| Spotify | Live | Live (audio-features has genre fallback) | Auto-trigger on 2nd provider | OauthView card + SpotifyPhysics |
| X/Twitter | Live | Live (PKCE) + LLM psychoanalysis | Auto-trigger on 2nd provider | OauthView card + UniverseView |
| Strava | Live | Live (activities + stats) | Auto-trigger on 2nd provider | OauthView card |
| Google Calendar | Live (OAuth) | Live (temporal patterns) | Included in synthesis | OauthView — no card yet (handled by callback) |
| Co-Star | Backend built | Credential proxy (no OAuth) | Included if present | OauthView card (CoStarConnect component) |
| Letterboxd | Backend built | API key auth + username ingest | Included if present | OauthView card (LetterboxdConnect component) |
| Steam | Backend built | OpenID 2.0 + game library | Included if present | OauthView card (SteamConnect component) |

## Infrastructure

- **Pinecone**: Index `channelzero`, 3 namespaces (users, journal, images), embeddings via `text-embedding-3-small` (OPENAI_EMBED_KEY)
- **Migrations**: SQL files in `server/migrations/`, tracked in `_migrations` table, run via `python -m server.app.migrate`
- **Frontend deploy**: Vercel auto-deploy from main (`channelzero.vercel.app`)
- **Backend deploy**: Render auto-deploy from main (`channelzero-api.onrender.com`)
- **Database**: Neon PostgreSQL (pooled + unpooled connections)

## Known Issues

- **Spotify audio features deprecated**: Fallback active (genre→valence mapping + track popularity as energy proxy)
- **Tone.js + Matter.js**: Matter.js on npm (migrated from CDN 2026-04-20), Tone.js still CDN — no version lock
- **Manual migrations**: No CI runs them. New SQL files require manual trigger on Render
- **No TypeScript CI**: `vue-tsc --noEmit` not in deploy pipeline
- **OpenAI API key**: Was returning 403 as of 2026-04-20 (`proj_8pERhmljbOUkRzurStcMGtZ5`)
- **Psychometrics scoring stubbed**: IPIP-NEO and ECR-R return placeholder values in `scoring.py`

## Recent Changes (2026-04-21)

- Oracle synthesis auto-triggers when user connects 2nd+ provider (pulls real JSONB data)
- Oracle PsychCoordinate persisted to `vibe_vectors.oracle_coordinate` (was Pinecone-only)
- Cross-provider match scoring: Twitter overlap, Strava overlap, Oracle insight in match response
- Universe view planets reflect Oracle synthesis state
- Game view match cards show cross-provider signal lines
- Admin insights panel: archetype distribution, attachment styles, connector depth histogram
- Zeromind trance sessions stored in `vibe_vectors.zeromind_data`
