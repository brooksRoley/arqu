# Connector Results Pages — Design Spec

## Overview

Each connected data connector gets a dedicated results page accessible from `/calibrate`. The page is a cinematic narrative scroll with physics-driven, data-reactive animations visualizing the ingested data, an LLM-generated narrative ("our read"), structured data cards, raw JSON, and explicit cross-connector correlations.

## Architecture: One Generic Component, Per-Provider Config

A single `ConnectorResultView.vue` handles all 11 connectors (Steam excluded). A `connectorConfig.ts` file contains a config object per provider defining labels, colors, stat fields, tag fields, and physics-to-data mappings.

### Routes

- **New route:** `/calibrate/:provider` — auth required
- **Valid providers:** spotify, twitter, strava, google, github, youtube, reddit, letterboxd, instagram, tiktok, costar
- **Link from:** Connected cards on `/calibrate` (OauthView.vue) get a clickable link/button to `/calibrate/:provider`

### Data Flow

1. `GET /api/:provider/profile` — existing endpoints (raw JSON data)
2. `GET /api/:provider/analyze` — LLM-generated narrative (exists for twitter; needs building for other 10)
3. `GET /api/connectors/correlations?provider=:provider` — cross-connector links (new endpoint)

## Page Layout (5 Scroll Sections)

### 1. Hero — Physics Canvas + Title
- Full-viewport Matter.js canvas as background
- Provider name + subtitle overlaid (e.g. "Spotify — The Sonic Blueprint")
- Particles/orbs driven by data values via physics config mapping
- Subtle scroll indicator at bottom
- Canvas parallax-fades to ~20% opacity when scrolling past, continues behind content

### 2. The Read — LLM Narrative
- `/analyze` response rendered as flowing prose
- Monospace font, muted color, generous line-height
- Text fades in paragraph by paragraph on scroll

### 3. Signal Data — Structured Cards
- Hero stats as large numbers with labels (from `heroStats` config)
- Tag fields as pill lists (from `tagFields` config)
- Bar/meter visualizations for 0-1 range values
- Cards fade and slide in on scroll via Intersection Observer

### 4. Raw Signal — Pretty JSON
- Collapsible section showing full profile JSON
- Syntax-highlighted, monospace
- Starts collapsed, click to expand

### 5. Cross-Signal Correlations
- List of explicit connector-to-connector data point links
- Each shows: provider icon + field name + value arrow provider icon + field name + value
- Short explanation per correlation
- e.g. "Spotify energy (0.73) <-> Strava avg HR (162)" — "High sonic intensity mirrors physical exertion patterns"

## Provider Config Shape

```ts
interface ProviderConfig {
  key: string
  label: string
  subtitle: string
  color: string
  heroStats: { field: string; label: string; format: 'decimal' | 'integer' | 'percent' }[]
  tagFields: { field: string; label: string }[]
  physics: {
    particleSpeed: string   // data field path
    colorTemp: string       // data field path
    particleCount: string   // data field path
    pulseRate: string       // data field path
    sizeVariance?: string   // optional data field path
  }
}
```

### Physics-to-Data Mappings

| Visual Property | What It Controls | Range |
|---|---|---|
| particleSpeed | Velocity of orbs/particles | Slow drift to fast swarm |
| colorTemp | Color palette | Cool blues/purples (low) to warm ambers/pinks (high) |
| particleCount | Number of particles | Sparse to dense field |
| pulseRate | Background/particle pulse frequency | Slow throb to rapid pulse |
| sizeVariance | Particle size distribution | Uniform to varied |

Default mappings for connectors without obvious physics fields (GitHub, Reddit, etc.):
- particleCount: number of items (repos, subreddits, films)
- particleSpeed: activity frequency
- colorTemp: provider brand color with brightness from engagement metrics
- pulseRate: derived from temporal data if available

### Scroll Animations (CSS)
- Intersection Observer triggers fade-in + slight upward slide per section
- Number stats count up from 0 when entering viewport
- Progress bars/meters fill when visible

## Backend Work Required

### New `/analyze` Endpoints (10 connectors)

Follow the existing Twitter `/analyze` pattern: hit the LLM with the user's profile data, return a psychological/behavioral narrative. Store the result so subsequent loads don't re-call the LLM.

Connectors needing `/analyze`: spotify, strava, google (gcal), github, youtube, reddit, letterboxd, instagram, tiktok, costar

### New Correlations Endpoint

`GET /api/connectors/correlations?provider=:provider`

Returns an array of cross-connector links:
```json
[
  {
    "source": { "provider": "spotify", "field": "audio_avg.energy", "value": 0.73, "label": "Energy" },
    "target": { "provider": "strava", "field": "avg_heartrate", "value": 162, "label": "Avg HR" },
    "explanation": "High sonic intensity mirrors physical exertion patterns"
  }
]
```

This endpoint queries the user's `vibe_vectors` row, checks which providers have data, and uses the LLM to generate correlations between the specified provider and all other connected providers.

## Files to Create/Modify

### New Files
- `src/views/ConnectorResultView.vue` — the generic results page
- `src/config/connectorConfig.ts` — per-provider config objects
- `server/app/connectors/router.py` — correlations endpoint

### Modified Files
- `src/router/index.ts` — add `/calibrate/:provider` route
- `src/views/OauthView.vue` — add links to results pages from connected cards
- `server/app/main.py` — register connectors router
- `server/app/spotify/router.py` — add `/analyze` endpoint
- `server/app/strava/router.py` — add `/analyze` endpoint
- `server/app/gcal/router.py` — add `/analyze` endpoint
- `server/app/github/router.py` — add `/analyze` endpoint
- `server/app/youtube/router.py` — add `/analyze` endpoint
- `server/app/reddit/router.py` — add `/analyze` endpoint
- `server/app/letterboxd/router.py` — add `/analyze` endpoint
- `server/app/instagram/router.py` — add `/analyze` endpoint
- `server/app/tiktok/router.py` — add `/analyze` endpoint
- `server/app/costar/router.py` — add `/analyze` endpoint
