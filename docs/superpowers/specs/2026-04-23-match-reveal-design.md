# Match Reveal + Fitting Ritual — Design Spec
**Date:** 2026-04-23
**Status:** Approved

## Overview

Build the product's missing reveal moment: a scroll-narrative surface that shows a matched pair *why* the system paired them, using every signal layer (Spotify, Oracle, psychometrics, Strava, Twitter, fitting avatars). Before the first reveal, users complete a two-phase "fitting ritual" — building a self-avatar and an ideal-partner avatar — whose overlap with their match becomes part of the story.

The reveal is the single interaction that converts ChannelZero's thesis from a promise into a felt experience.

---

## Routes

| Route | Auth | Purpose |
|---|---|---|
| `/fitting/:matchId` | yes | Two-phase avatar builder (self + ideal) before first reveal |
| `/reveal/:matchId` | yes | Scroll-narrative match reveal |

`matchId` is the UUID of the matched user (the other person in the mutual match pair).

---

## Entry Points

### Post-mutual-match (primary)
When `POST /api/match/interact` returns `mutual_match: true`, GameView redirects to `/fitting/:matchId` (if fitting incomplete) or `/reveal/:matchId` (if fitting already done).

### From messages (revisit)
Each mutual match in MessagesView and ThreadView gets a "Signal Story" link that navigates to `/reveal/:matchId`. Revisits always skip fitting and go directly to the reveal scroll.

### From messages list (new matches indicator)
`GET /api/match/new` already returns unseen mutual matches. The messages list can surface a "New match — view reveal" prompt linking to `/fitting/:matchId`.

---

## Pre-Reveal: Fitting Ritual

### Purpose
Capture the user's self-image and desire-image at the emotionally loaded moment right before seeing their match. The delta between what they project and what they desire is psychologically revealing, and the overlap between their ideal and their match's self-avatar is the most concrete proof of alignment.

### Flow
1. User lands on `/fitting/:matchId`
2. If `fitting_self` exists in `vibe_vectors`, skip to step 4
3. **Phase 1 — "Show us you"**: Full body configurator (body type, height, build, chest, waist, hips, shoulders, skin tone, hair color/length, suit style/color). On submit, stores to `vibe_vectors.fitting_self`
4. If `fitting_ideal` exists, redirect to `/reveal/:matchId`
5. **Phase 2 — "Show us what you see"**: Same configurator, fresh state, different framing ("Build the person you imagine"). On submit, stores to `vibe_vectors.fitting_ideal`
6. Redirect to `/reveal/:matchId`

### Configurator Data Shape
```typescript
interface FittingData {
  body_type: 'female' | 'male'
  height: number        // inches (56–82)
  build: number         // 1–10
  chest: number         // inches (26–58)
  waist: number         // inches (22–58)
  hips: number          // inches (28–64)
  shoulders: number     // inches (14–24)
  skin_color: string    // hex
  skin_shadow: string   // hex
  hair_color: string    // hex
  hair_length: 'short' | 'medium' | 'long'
  suit_color: string    // hex
  suit_color_dark: string // hex
  // Female-specific
  top_style?: 'underwire' | 'bralette' | 'bandeau' | 'halter'
  rise?: 'low' | 'mid' | 'high' | 'ultra'
  coverage?: 'cheeky' | 'moderate' | 'full' | 'boy-short'
  // Male-specific
  top?: 'none' | 'rash-short' | 'rash-long' | 'tank'
  bottom?: 'board-above' | 'board-knee' | 'board-below' | 'trunk'
  wetsuit?: 'none' | 'shorty' | 'spring' | 'full'
}
```

### Storage
Two new JSONB columns on `vibe_vectors`:
- `fitting_self JSONB DEFAULT NULL`
- `fitting_ideal JSONB DEFAULT NULL`

### Reuse from Fitting.vue
The existing `Fitting.vue` component (35 kb) contains all SVG rendering logic for both male and female body types, skin tones, hair options, suit styles, measurement sliders, and the interactive zone-highlight system. Extract the core rendering and controls into a shared composable or component that both the standalone `/fitting` route and the new `/fitting/:matchId` ritual can use.

---

## The Reveal Scroll

A single-page vertical scroll narrative. Each section occupies roughly one viewport height and fades in as the user scrolls into it. Five sections, each revealing a deeper layer of alignment.

### Section 1 — Signal Silhouettes
**Full viewport.** Two aura-field silhouettes side by side, one per user.

Each silhouette is a body-shaped form (derived from the user's `fitting_self` proportions) surrounded by colored aura layers. Each aura ring represents a signal type:

| Signal | Aura Color | Ring Position |
|---|---|---|
| Psychometric (Big Five, ECR-R) | Purple (#8B5CF6) | Innermost |
| Oracle (7D coordinates) | Pink (#EC4899) | Second |
| Spotify (audio features, genres) | Green (#22C55E) | Third |
| Attachment / Intake | Gold (#F59E0B) | Fourth |
| Activity (Strava, Steam) | Blue (#3B82F6) | Outermost |

Aura intensity (opacity, blur radius) per layer is proportional to signal strength — a user with rich Spotify data has a vivid green ring; one with no Strava data has no blue ring at all.

Where two people's auras overlap (center of the viewport), the colors blend. This is purely visual — the "overlap zone" is rendered by positioning the two silhouettes close enough that their outer rings intersect.

**Data needed:** Both users' `fitting_self` (for silhouette shape) + which signal layers each user has populated (boolean flags from `vibe_vectors`).

### Section 2 — Desire Overlap
**Two comparison pairs, stacked vertically.**

**Pair A — "What you imagined / Who they are":**
Left: the current user's `fitting_ideal` avatar rendered as SVG. Right: the match's `fitting_self` avatar. Between them, a simple overlap readout:

```
Body type match: ✓
Build proximity: 82%
Proportions: 74%
Coloring: close
```

Overlap is computed client-side from the fitting data:
- Build proximity: `1 - |self.build - ideal.build| / 9`
- Proportions: average of per-dimension proximities (chest, waist, hips, shoulders, height), each `1 - |a - b| / range`
- Coloring: hex distance between skin colors, bucketed into "close", "moderate", "different"
- Body type match: boolean

**Pair B — "What they imagined / Who you are":**
Same layout, reversed. The match's `fitting_ideal` vs the current user's `fitting_self`.

**Data needed:** Both users' `fitting_self` + `fitting_ideal`.

### Section 3 — Signal Layers
**Card-based breakdown.** Only renders cards for signal types where both users have data.

**Spotify Card:**
- Shared genres as pill badges (indigo)
- Shared artists as pill badges (green)
- Audio feature delta bars — for each of valence, energy, danceability, acousticness, instrumentalness: show both users' values as overlapping bars on the same track (user = purple, match = pink)
- Tempo comparison: plain numbers side by side

**Oracle Card:**
- 7D coordinate paired bars — empathy_index, isolation_metric, fatalism_score, masochism_curve
- Oracle rationale text (the LLM-generated analysis of why these coordinates align)

**Strava Card:**
- Shared activity types (pill badges)
- Their activity types you don't share (muted)

**Twitter Card:**
- Communication style match (from `twitter_overlap`)
- Shared language patterns

**Steam Card:**
- Shared game genres or play patterns (if both have Steam data)

Each card follows the same structural pattern: header with signal icon + name, content area, muted "only you" / "only them" section for asymmetric data.

**Data needed:** Both users' provider data from `vibe_vectors` (spotify_data, twitter_data, strava_data, steam_data, oracle_coordinate).

### Section 4 — Psychometric Alignment
**Paired comparison bars + text.**

**Big Five (IPIP-NEO):** Five paired horizontal bars. Each bar shows both users' scores on the same 0–1 track. Labels: Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism. Color: user = purple, match = pink.

**ECR-R Attachment:** Two paired bars — Attachment Anxiety, Attachment Avoidance. Same visual treatment.

**Pill badges row:** Love Language (both), Values Cluster (both), Sociosexual Orientation (both). Matching values get a highlight ring.

**Narrative block:** The Oracle's psychoanalytic narrative for the match, displayed as a quoted text block. This is the `match_reason` from the intake match endpoint combined with `oracle_rationale` if available.

**Data needed:** Both users' `user_psychometrics` rows + `oracle_coordinate` from `vibe_vectors`.

### Section 5 — Connect
**Centered, minimal.**

- Large compatibility percentage: `Math.round(similarity * 100)%` from Pinecone cosine similarity
- Match reason text (1-2 sentences, from `match_reason`)
- CTA button: "Send a message" → navigates to `/messages/:matchId`
- Secondary link: "Back to matches" → navigates to `/game`

**Data needed:** `similarity` score + `match_reason` from the match data.

---

## Backend

### New endpoint: `GET /api/match/reveal/{target_id}`

**Auth:** `get_current_user_id` dependency. Validates that a mutual match exists between the current user and `target_id`.

**Returns:**
```json
{
  "similarity": 0.87,
  "match_reason": "string",
  "self": {
    "user_id": "uuid",
    "display_name": "string",
    "fitting_self": { ... },
    "fitting_ideal": { ... },
    "spotify_data": { ... },
    "oracle_coordinate": { ... },
    "strava_data": { ... },
    "twitter_data": { ... },
    "steam_data": { ... },
    "has_spotify": true,
    "has_oracle": true,
    "has_strava": false,
    "has_twitter": true,
    "has_steam": false
  },
  "match": {
    "user_id": "uuid",
    "display_name": "string",
    "fitting_self": { ... },
    "fitting_ideal": { ... },
    "spotify_data": { ... },
    "oracle_coordinate": { ... },
    "strava_data": { ... },
    "twitter_data": { ... },
    "steam_data": { ... },
    "has_spotify": true,
    "has_oracle": true,
    "has_strava": true,
    "has_twitter": false,
    "has_steam": false
  },
  "psychometrics": {
    "self": {
      "ipip_neo_scores": { "O": 0.7, "C": 0.5, "E": 0.6, "A": 0.8, "N": 0.3 },
      "ecr_r_scores": { "anxiety": 0.4, "avoidance": 0.2 },
      "love_language": "quality_time",
      "values_cluster": "growth",
      "sociosexual_orientation": "restricted"
    },
    "match": {
      "ipip_neo_scores": { "O": 0.8, "C": 0.6, "E": 0.5, "A": 0.7, "N": 0.4 },
      "ecr_r_scores": { "anxiety": 0.3, "avoidance": 0.3 },
      "love_language": "physical_touch",
      "values_cluster": "growth",
      "sociosexual_orientation": "moderate"
    }
  }
}
```

**Query logic:**
1. Verify mutual match in `match_interactions` (both accepted)
2. Fetch both users' `vibe_vectors` rows (fitting, provider data, oracle coordinates)
3. Fetch both users' `user_psychometrics` rows
4. Fetch similarity score by querying Pinecone with the current user's vector and checking the match's score in results (same approach as `/api/intake/match`)
5. Generate `match_reason` text using the same logic as the intake match endpoint (attachment/defense alignment + oracle empathy + similarity score)

**Sensitivity:** Provider data for the match user is read-only and scoped — raw tokens are never exposed. Only the processed signal data (genres, audio averages, activity types) is returned.

### New endpoint: `POST /api/intake/fitting`

**Auth:** `get_current_user_id` dependency.

**Request body:**
```json
{
  "phase": "self" | "ideal",
  "data": { FittingData }
}
```

**Logic:** Updates `vibe_vectors.fitting_self` or `vibe_vectors.fitting_ideal` for the current user.

### New migration

```sql
ALTER TABLE vibe_vectors
  ADD COLUMN fitting_self JSONB DEFAULT NULL,
  ADD COLUMN fitting_ideal JSONB DEFAULT NULL;
```

---

## Frontend Components

### New files:
- `src/views/FittingRitualView.vue` — Two-phase fitting flow wrapping the existing configurator
- `src/views/RevealView.vue` — Scroll-narrative reveal
- `src/components/AuraField.vue` — SVG aura-field silhouette renderer (reusable)
- `src/components/FittingAvatar.vue` — Extracted SVG body renderer from Fitting.vue (shared between standalone fitting and ritual)
- `src/components/SignalCard.vue` — Card component for Section 3 signal layers
- `src/components/PairedBar.vue` — Paired horizontal bar component (user vs match on 0–1 scale)

### Composable:
- `src/composables/useRevealStore.ts` — Fetches and caches reveal data for a match pair

### Router additions:
```typescript
{
  path: '/fitting/:matchId',
  name: 'fitting-ritual',
  component: () => import('@/views/FittingRitualView.vue'),
  meta: { requiresAuth: true }
},
{
  path: '/reveal/:matchId',
  name: 'reveal',
  component: () => import('@/views/RevealView.vue'),
  meta: { requiresAuth: true }
}
```

### Modifications to existing files:
- `GameView.vue` — On mutual match, redirect to `/fitting/:matchId` instead of showing inline banner
- `MessagesView.vue` — Add "Signal Story" link per mutual match
- `ThreadView.vue` — Add "Signal Story" link in thread header

---

## Scroll Behavior

Each section uses Intersection Observer to trigger fade-in animations:
- Sections start with `opacity: 0; transform: translateY(24px)`
- On intersect (threshold 0.15): transition to `opacity: 1; transform: translateY(0)` over 600ms
- No scroll-jacking, no snap points — natural scroll with gentle reveal pacing

---

## Error & Empty States

- **No fitting data yet:** Redirect from `/reveal/:matchId` to `/fitting/:matchId`
- **Match not mutual:** 403 from reveal endpoint → redirect to `/game` with toast "This match hasn't been confirmed yet"
- **Missing signal layers:** Sections 3 and 4 gracefully omit cards for signal types where one or both users have no data. If zero shared signals exist, show a muted "Connect more signals to enrich your match story" placeholder
- **Psychometrics not completed:** Section 4 shows "Complete your psychometric assessment to unlock this layer" with link to `/psychoanalysis`

---

## Out of Scope

- Animated intro sequence (decided: scroll narrative only, no phased animation)
- Population-level comparisons ("you're more open than 80% of users")
- Real-time updates if either user adds new signal data after reveal
- Match quality scoring beyond Pinecone cosine similarity
- Notifications / push for new mutual matches
- Fitting data contributing to the Pinecone vibe vector (future enhancement — for now it's stored but not embedded)
