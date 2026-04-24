# Post-Trance Microdose — Design Spec

> Psychometric questions delivered 1-2 at a time as a frosted glass overlay after zeromind trance sessions, paired with connector data reflection (Spotify/Strava).

## Problem

1. Psychometric assessment (`/psychoanalysis`) dumps 17 items at once — feels clinical, not ritual
2. Strava data is ingested silently and never shown back to the user
3. Spotify data is only visible on `/spotify` — disconnected from the trance experience
4. Zeromind sessions end abruptly after wake phase with no debrief or reflection

## Design Decisions

- **1-2 items per dose** — liminal, not clinical
- **Frosted glass overlay** — card floats over fading trance visualization, preserving atmosphere
- **Connector-specific deep dive** — each session picks one connected source, shows 2-3 data points, links the psychometric item thematically
- **Infinite cycle** — core 17 items first, then extended instruments (longer IPIP-NEO, full ECR-R, new instruments). The overlay is a permanent feature of post-trance.
- **Zeromind first** — only ZeromindView gets the overlay initially. Spiral/hypno can adopt later.

## Question Pool & Selection

### Core Pool (17 items, distributed first)

Existing items from PsychoanalysisView, tagged with `connector_affinity`:

**IPIP-NEO (10 items, likert_5):**
| item_id | text | affinity |
|---------|------|----------|
| ipip_neo_0 | I have a rich imagination | spotify |
| ipip_neo_1 | I am always prepared | strava |
| ipip_neo_2 | I am the life of the party | spotify |
| ipip_neo_3 | I sympathize with others' feelings | general |
| ipip_neo_4 | I get stressed out easily | general |
| ipip_neo_5 | I see beauty in things others might not notice | spotify |
| ipip_neo_6 | I pay attention to details | strava |
| ipip_neo_7 | I feel comfortable around people | general |
| ipip_neo_8 | I take time out for others | general |
| ipip_neo_9 | I worry about things | general |

**ECR-R (4 items, likert_7):**
| item_id | text | affinity |
|---------|------|----------|
| ecr_r_0 | I worry about being abandoned | general |
| ecr_r_1 | I need a lot of reassurance that I am loved | general |
| ecr_r_2 | I prefer not to share my deepest feelings | strava |
| ecr_r_3 | I feel comfortable depending on others | general |

**Identity (3 items, categorical):**
| item_id | text | type | options | affinity |
|---------|------|------|---------|----------|
| identity_love_language | What makes you feel most valued? | buttons | Words of Affirmation, Quality Time, Gifts, Acts of Service, Physical Touch | general |
| identity_values | What drives you most? | buttons | Traditional, Career-driven, Creative, Progressive, Adventure, Spiritual | strava |
| identity_sociosexual | How do you approach intimacy? | buttons | Restricted, Moderate, Unrestricted | general |

### Extended Pool (infinite, after core)

Deeper instruments added server-side without frontend changes:
- Full IPIP-NEO (120 items → remaining 110)
- Full ECR-R (36 items → remaining 32)
- Dark Triad short form (12 items)
- Locus of Control (10 items)
- Emotional Granularity (8 items)

### Selection Logic

1. Pick connector: round-robin among connected providers, tracked in localStorage (`cz-last-reflect-connector`)
2. Query `GET /api/psychometrics/next-item?connector=<picked>`
3. Backend finds next unanswered item with matching `connector_affinity`, falling back to `general`
4. If core pool exhausted, pulls from extended pool
5. Returns `null` when everything answered (overlay becomes data-only)

## Data Surfacing Cards

### Spotify (2-3 stats per session, varied)

Picked from available data:
- Top genre + second genre (e.g., "shoegaze · dream pop")
- Valence with poetic label: <0.3 "melancholic", 0.3-0.6 "bittersweet", >0.6 "luminous"
- Energy vs acousticness narrative ("high energy, low acoustic — you like it loud")
- A top artist name

### Strava (2-3 stats per session, varied)

Picked from available data:
- Dominant activity + count ("42 runs")
- Total distance with comparison ("312 km — London to Paris")
- Avg heartrate paired with trance coherence ("HR 145 bpm · coherence 87")
- Elevation framed poetically ("3,400m climbed")

### Trance Session (always shown)

Single dim line: "coherence 87 · 7m 23s · theta"

## Backend

### New Table: `psychometric_responses`

```sql
CREATE TABLE psychometric_responses (
    user_id UUID NOT NULL REFERENCES users(id),
    item_id TEXT NOT NULL,
    value INT NOT NULL,
    connector_context TEXT,
    trance_coherence FLOAT,
    session_duration_ms INT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, item_id)
);
```

UPSERT on `(user_id, item_id)` — re-answering replaces old response.

### New Endpoint: `POST /api/psychometrics/microdose`

Request:
```json
{
  "item_id": "ipip_neo_3",
  "value": 4,
  "connector_context": "spotify",
  "trance_coherence": 87.2,
  "session_duration_ms": 450000
}
```

Response: `204 No Content`

Side effect: after enough items accumulate for a given instrument (all 10 IPIP-NEO, all 4 ECR-R), auto-compute scores and upsert into `user_psychometrics`. Partial profiles are fine — compute what's available.

### New Endpoint: `GET /api/psychometrics/next-item?connector=spotify`

Response:
```json
{
  "item_id": "ipip_neo_3",
  "instrument": "ipip_neo",
  "text": "I see beauty in things others might not notice",
  "scale": "likert_5",
  "connector_affinity": "spotify",
  "progress": { "answered": 6, "core_total": 17 }
}
```

Returns `null` body when no items remain.

### New Endpoint: `GET /api/strava/profile`

Returns `vibe_vectors.strava_data` as JSON. Mirrors existing `/api/spotify/profile` pattern.

## Frontend

### PostTranceOverlay.vue

**Props:**
- `coherence: number`
- `syncCount: number`
- `sessionDuration: number` (ms)
- `dominantPhase: string`

**Behavior:**
1. On mount, picks connector (round-robin via localStorage)
2. Fetches `next-item` and connector profile in parallel
3. Fades in over 1.5s
4. Renders: connector data card → trance line → psychometric item → submit
5. On submit: POST microdose, fade out over 1s
6. Dismiss: click outside or × button (answer is optional)
7. If no question available: data-only reflection (no question section)

**Visual:**
- `backdrop-filter: blur(16px)` frosted glass card
- Dark bg with slight transparency
- Max-width ~400px, centered
- Connector stats in small muted type
- Likert scale as horizontal button group (1-5 or 1-7)
- Categorical items as vertical button stack
- Thin progress bar at bottom: "6 / 17"

### ZeromindView Integration

- `completeSession()` sets `showOverlay = true`
- `<PostTranceOverlay v-if="showOverlay" ... @close="showOverlay = false" />`
- Overlay renders above the canvas layers

## Migration

`017_psychometric_responses.sql` — creates the new table.

## Question Pool Storage

The question pool lives in a Python module `server/app/psychometrics/question_pool.py` as a list of dicts. No database table needed — the pool is code, extended via PRs. The `next-item` endpoint queries `psychometric_responses` for answered items and returns the next unanswered one from the pool.

## Route Map Updates

No new routes. PostTranceOverlay is a component inside ZeromindView, not a page. `GET /api/strava/profile` follows existing pattern.
