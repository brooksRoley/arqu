# Admin Insights Panel — Design Spec
**Date:** 2026-04-17
**Status:** Approved

## Overview

Extend the existing `/admin` view with two new scrollable sections below the users table: **Spotify Profiles** and **Psychometrics**. Each section displays per-user cards with rich signal data that is currently stored in the database but not surfaced in any UI.

---

## Architecture

### Backend — two new endpoints in `/server/app/analytics/router.py`

**`GET /api/analytics/spotify-profiles?page=1&per_page=20`**
- Requires `require_admin` dependency
- Joins `users` + `vibe_vectors` on `user_id`
- Filters: `vibe_vectors.spotify_data IS NOT NULL`
- Returns paginated list of per-user Spotify cards
- Response shape per item:
  ```json
  {
    "user_id": "uuid",
    "display_name": "string",
    "email": "string",
    "created_at": "timestamp",
    "top_artists": ["string", ...],
    "genres": ["string", ...],
    "audio_avg": {
      "valence": 0.0,
      "energy": 0.0,
      "danceability": 0.0,
      "acousticness": 0.0,
      "instrumentalness": 0.0,
      "tempo": 0.0
    }
  }
  ```
- Response envelope: `{ items: [...], total: int, page: int, per_page: int }`

**`GET /api/analytics/psychometrics?page=1&per_page=20`**
- Requires `require_admin` dependency
- Joins `users` + `user_psychometrics` on `user_id`
- Filters: `user_psychometrics` row exists for user
- Returns paginated list of per-user psychometric cards
- Response shape per item:
  ```json
  {
    "user_id": "uuid",
    "display_name": "string",
    "email": "string",
    "created_at": "timestamp",
    "ipip_neo_scores": { "O": 0.0, "C": 0.0, "E": 0.0, "A": 0.0, "N": 0.0 },
    "ecr_r_scores": { "anxiety": 0.0, "avoidance": 0.0 },
    "love_language": "string",
    "sociosexual_orientation": "string",
    "values_cluster": "string",
    "narrative": "string"
  }
  ```
- Response envelope: `{ items: [...], total: int, page: int, per_page: int }`

### Frontend — `useAdminStore.ts`

New state:
```typescript
spotifyProfiles: SpotifyProfile[]
spotifyTotal: number
spotifyPage: number

psychometrics: PsychometricProfile[]
psychometricsTotal: number
psychometricsPage: number
```

New methods:
- `fetchSpotifyProfiles(page?: number)` — calls `/api/analytics/spotify-profiles`
- `fetchPsychometrics(page?: number)` — calls `/api/analytics/psychometrics`

The existing `refresh()` method triggers all five fetches (funnel, connectors, users, spotify, psychometrics).

### Frontend — `AdminView.vue`

Two new sections appended below the users table, each following the same structural pattern as existing sections:
- Section header with title + count
- Card grid (responsive, ~3 cols on desktop)
- Pagination controls (prev/next with page indicator)

---

## Spotify Profiles Section

**Section header:** "Spotify Profiles" + `(N connected)`

**Per-user card contains:**
- Avatar initial (first letter of display_name, or email if display_name is null) + display name + email (muted) + joined date
- **Top Artists:** up to 3 artist names as pill badges (indigo/purple tones)
- **Top Genres:** up to 5 genre names as pill badges (smaller, muted)
- **Audio Bars** — 5 labeled progress bars (0–1 scale):
  - Valence — color: amber/yellow (happiness signal)
  - Energy — color: red/orange
  - Danceability — color: green
  - Acousticness — color: blue
  - Instrumentalness — color: purple
- **Tempo:** plain number display (e.g., `124 BPM`)

Cards paginate at 20/page. Users without `spotify_data` are excluded entirely.

---

## Psychometrics Section

**Section header:** "Psychometric Profiles" + `(N assessed)`

**Per-user card contains:**
- Avatar initial (first letter of display_name, or email if null) + display name + email (muted)
- **Big Five Bars** — 5 labeled progress bars (0–1 scale):
  - Openness (O)
  - Conscientiousness (C)
  - Extraversion (E)
  - Agreeableness (A)
  - Neuroticism (N)
- **ECR-R** — 2 bars:
  - Attachment Anxiety
  - Attachment Avoidance
- **Pill badges:** Love Language + Values Cluster + Sociosexual Orientation
- **Narrative:** LLM-generated psychoanalysis quoted in a text block, truncated to ~3 lines with a toggle to expand

Cards paginate at 20/page. Users without a `user_psychometrics` row are excluded entirely.

---

## Error Handling

- If an endpoint returns an error, the section shows an inline error message (same pattern as existing admin error state)
- Empty state: if no users have Spotify connected / no psychometrics exist, show a muted "No data yet" placeholder card
- Pagination buttons disabled when on first/last page

---

## Out of Scope

- Population-level aggregates (genre frequency, average valence across all users)
- User detail drawer / single-user deep dive
- Oracle coordinate visualization (empathy, isolation, fatalism, masochism)
- Match quality analytics
- Karma ledger breakdown
