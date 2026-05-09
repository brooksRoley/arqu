# Personality Observatory — Progressive Psychometric Deepening

## Overview

Replace the static Big Five / ECR-R score display on `/psychoanalysis` with a canvas-rendered cosmic radar visualization. Users start with 10-item short-form domain scores, then progressively unlock 30 IPIP-NEO facets and 6 ECR-R depth levels by answering items through trance microdose sessions and an active drill mode.

## Data Architecture

### Item Banks

**Core pool (existing, unchanged):** 10 IPIP-NEO short-form items (2 per domain) + 4 ECR-R short-form items + 3 identity categoricals = 17 items. These provide domain-level Big Five scores and baseline attachment scores from day one.

**Deep pool (new):** 120 published Johnson IPIP-NEO-120 items + 36 published Fraley ECR-R-36 items = 156 items. Each carries a `facet` field.

### Facet Structure

**IPIP-NEO:** 5 domains x 6 facets x 4 items = 120 items, 30 unlockable facet nodes.

| Domain | Facets |
|--------|--------|
| N (Neuroticism) | Anxiety, Anger, Depression, Self-Consciousness, Immoderation, Vulnerability |
| E (Extraversion) | Friendliness, Gregariousness, Assertiveness, Activity Level, Excitement-Seeking, Cheerfulness |
| O (Openness) | Imagination, Artistic Interests, Emotionality, Adventurousness, Intellect, Liberalism |
| A (Agreeableness) | Trust, Morality, Altruism, Cooperation, Modesty, Sympathy |
| C (Conscientiousness) | Self-Efficacy, Orderliness, Dutifulness, Achievement-Striving, Self-Discipline, Cautiousness |

**ECR-R:** 2 subscales x 18 items = 36 items. Presented as 3 depth levels per subscale (6 items each), 6 unlockable depth nodes.

### Unlock Threshold

A facet node unlocks only when all 4 items for that facet are answered (full accuracy, no partial scores). An ECR-R depth level unlocks when all 6 items in that level are answered.

### Deep Pool Item Schema

Extends existing `PoolItem` with a `facet` field:

```python
class DeepPoolItem(TypedDict):
    item_id: str          # "ipip_deep_{domain}_{facet}_{0-3}" or "ecr_r_deep_{subscale}_{level}_{0-5}"
    instrument: str       # "ipip_neo_deep" or "ecr_r_deep"
    text: str             # Published item text (public domain)
    scale: str            # "likert_5" (IPIP) or "likert_7" (ECR-R)
    options: None
    connector_affinity: str  # "general" for all deep items
    trait: str            # "O","C","E","A","N" or "anxiety","avoidance"
    facet: str            # e.g., "imagination", "assertiveness", "level_1"
    direction: int        # +1 or -1, from published reverse-scoring key
```

Item `direction` values align 1:1 with the existing `_IPIP_NEO_120_REVERSE` and `_ECR_R_36_REVERSE` sets in `scoring.py`.

**Item text sourcing:** The 120 IPIP-NEO items are public domain and published at ipip.ori.org/newNEOKey.htm. The 36 ECR-R items are published in Fraley et al. (2000). Both must be transcribed into the `DEEP_POOL` with correct facet tags and direction flags. This is a mechanical but substantial data entry task (~156 items).

### Scoring

**Domain scores:** Computed from short-form items initially. As deep items accumulate, blended: `(short_form_score * short_count + deep_score * deep_count) / total_count`. When all 24 deep items for a domain are answered, domain score is computed purely from deep items.

**Facet scores:** Computed via the existing `_apply_key` infrastructure. A new `_score_facets()` function groups deep pool items by `(domain, facet)`, applies reverse-scoring, and returns per-facet normalized [0,1] scores. Only returns scores for fully answered facets (4/4 items).

**ECR-R depth scores:** Each depth level scored independently. Subscale score refines as levels unlock (same blending approach as domain scores).

### Storage

Deep items use the same `psychometric_responses` table and `/api/psychometrics/microdose` endpoint. No new tables. The `item_id` naming convention distinguishes deep items from core pool items.

### Item Selection Priority

`get_next_items()` extended with priority chain:

1. Unanswered core pool items (existing behavior, preserved)
2. Unanswered deep items, sorted by facet proximity to completion (3/4 > 2/4 > 1/4 > 0/4)
3. Within equal completion, round-robin across domains to avoid clustering

When in active drill mode for a specific domain, items are scoped to that domain's 24-item bank only, same proximity priority.

## Backend API

### New endpoint: `GET /api/psychometrics/facet-progress`

Returns the full observatory map state:

```json
{
  "domains": {
    "O": {
      "domain_score": 0.65,
      "facets": {
        "imagination": { "answered": 4, "required": 4, "score": 0.72, "unlocked": true },
        "artistic_interests": { "answered": 2, "required": 4, "score": null, "unlocked": false },
        "emotionality": { "answered": 0, "required": 4, "score": null, "unlocked": false }
      }
    }
  },
  "ecr_r": {
    "anxiety": {
      "subscale_score": 0.58,
      "depth_levels": [
        { "level": 1, "answered": 6, "required": 6, "score": 0.61, "unlocked": true },
        { "level": 2, "answered": 3, "required": 6, "score": null, "unlocked": false },
        { "level": 3, "answered": 0, "required": 6, "score": null, "unlocked": false }
      ]
    },
    "avoidance": {}
  },
  "total_answered": 42,
  "total_items": 156,
  "facets_unlocked": 7,
  "facets_total": 36
}
```

### Extended `/api/psychometrics/microdose` response

Adds an optional field when a facet completes:

```json
{
  "unlocked_facet": { "domain": "O", "facet": "imagination", "score": 0.72 }
}
```

Null when the submitted item does not complete a facet.

## Frontend — Psychoanalysis View Evolution

### Layout

The `/psychoanalysis` view is restructured:

- **Top:** LLM narrative (existing Oracle psychoanalytic reading)
- **Middle:** Personality Observatory canvas (cosmic radar replacing static score bars)
- **Bottom:** ECR-R orbital ring (attachment depth visualization)
- **Below canvas:** "Go Deeper" prompt when unanswered deep items exist, enters active drill mode

### State Transitions

1. **First visit (no data):** Canvas shows 5 domain hubs as dim outlines, all 30 facet nodes dormant. Prompt directs to short-form assessment.
2. **Short-form complete:** Domain hubs ignite with scores. All facet nodes remain dormant. Skeleton awaiting depth.
3. **Progressive unlock:** Facet nodes ignite one by one as microdose/drill items accumulate. Visual density grows session over session.
4. **Full unlock:** All 30 facets + 6 ECR-R depth nodes lit. Complete constellation.

### Canvas Visualization

A `usePersonalityPhysics` composable following the `useCosmicPhysics` pattern.

**Structure:**
- Five domain spokes radiate from center at 72-degree intervals
- 6 facet nodes per spoke, positioned center-outward
- Domain hub node at inner position of each spoke (always lit from short-form data)
- ECR-R ring: 6 nodes in outer orbit (3 anxiety, 3 avoidance), separate from Big Five radar

**Node states:**
- **Dormant:** Dark, faintly pulsing particles. Visible but inert.
- **Unlocked:** Domain-colored glow (N=blue, E=amber, O=violet, A=green, C=teal). Size scales with score (0.0 small/dim, 1.0 large/bright). Subtle orbital drift via Matter.js.

**Visual elements:**
- Connecting filaments: faint lines between hub and unlocked facet nodes, brighter as more facets complete. Fully dark spokes with no unlocks show as dotted/ghosted paths.
- Particle atmosphere: ambient drift between unlocked nodes via Matter.js physics

**Two-canvas overlay pattern:**
- Base canvas: Matter.js physics (node positions, drift, particle atmosphere)
- Overlay canvas: labels on unlocked nodes (facet name + score), progress HUD, tap targets

**Interaction:**
- Tap domain spoke: enters active drill mode (zooms/focuses on that domain)
- Tap unlocked facet node: tooltip with score + facet description
- Ambient: nodes drift subtly, particles flow between unlocked nodes

## Active Drill Mode

### Entry

User taps a domain spoke. Canvas zooms to that domain — other spokes dim, selected spoke expands to show 6 facet nodes with labels. Locked facets show names but no scores.

### Item Presentation

One item at a time, trance-style. Translucent overlay appears over dimmed canvas:

- Item text centered
- Likert-5 scale below (same interaction pattern as PostTranceOverlay microdose)
- Facet progress indicator: "Imagination - 2/4"
- After answering, next item fades in. No navigation chrome.

### Item Selection

Items drawn only from the selected domain's 24-item bank. Priority: facets closest to completion first.

### Facet Unlock Moment

When the 4th item for a facet is answered, the corresponding node ignites on the canvas behind the overlay — visible as a glow emerging through the translucent layer. Brief pause, then next item. The canvas is the feedback.

### Exit

Dismiss overlay at any point (tap outside / swipe down / escape). Progress saved. On exit, canvas zooms back to full five-spoke view with newly unlocked nodes glowing.

## Passive Microdose Integration

### Extended PostTranceOverlay Behavior

After core pool items are exhausted, `get_next_items()` draws from the deep pool. Same 5-items-per-session cadence.

**Priority in passive context:**
1. Remaining core pool items (existing behavior)
2. Deep items for facets closest to completion
3. Round-robin across domains at equal completion

### Unlock Notification in Trance Context

When a facet completes during trance microdose, PostTranceOverlay shows a brief glow pulse on the item card: "Imagination unlocked" — then continues. Subtle, doesn't break trance wind-down.

### Pacing

5 items per trance session. After core pool: ~22 sessions for full IPIP-NEO coverage, ~7 for ECR-R. Total ~29 trance sessions for full unlock, spread naturally over weeks.

## Files Affected

### Backend (new/modified)
- `server/app/psychometrics/question_pool.py` — add `DeepPoolItem` type, `DEEP_POOL` with 156 items, extend `get_next_items()` priority
- `server/app/psychometrics/scoring.py` — add `_score_facets()`, domain score blending logic
- `server/app/psychometrics/router.py` — add `GET /facet-progress` endpoint, extend `/microdose` response with `unlocked_facet`

### Frontend (new/modified)
- `src/composables/usePersonalityPhysics.ts` — new composable, cosmic radar canvas engine
- `src/views/PsychoanalysisView.vue` — replace static scores with observatory canvas, add drill mode overlay
- `src/components/PostTranceOverlay.vue` — handle deep pool items, facet unlock notification
