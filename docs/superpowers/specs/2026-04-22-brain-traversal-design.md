# Brain Traversal Layer — Design Spec
**Date:** 2026-04-22

## Overview

A spatial composition studio built on the existing brain image library. Users navigate their AI-generated image library through a UMAP-projected 2D map, traverse similarity paths to assemble sequences, and compose geometry, sound, and narration against those sequences — driven automatically by vibe dimension deltas extracted from embeddings. Output: MP4.

---

## Architecture

```
Ingest enhancement     → vibe dimensions + UMAP coords stored at upload time
Traversal UI           → /brain route: MapCanvas → LocalCanvas → Sequence strip
Composition layer      → vibe curve drives geometry, audio, transitions, narration → MP4
```

### New backend

| Addition | Detail |
|---|---|
| `brain_images.vibe_dimensions` | JSONB: `{ energy, warmth, density, intimacy, motion }` (0–1 each) |
| `brain_images.map_x`, `map_y` | FLOAT: UMAP 2D projection, normalized to 0–1000 unit square |
| `GET /api/brain/map` | Returns all user images with UMAP coords + vibe dims |
| `POST /api/brain/sequence/compose` | Takes ordered image IDs, returns per-transition descriptors |
| Migration `013_brain_vibe_dimensions.sql` | Adds new columns |

### New frontend composables

| Composable | Purpose |
|---|---|
| `useBrainMap` | Top-down canvas: pan/zoom, image thumbnails at UMAP positions |
| `useBrainLocal` | Local view: neighbor orbit arrangement, selection |
| `useBrainSequence` | Sequence strip state, vibe curve across sequence |
| `useBrainComposer` | Geometry/audio/narration driven by vibe curve |
| `useBrainExport` | Extends `useGlassExport` for multi-image sequence rendering |

---

## Section 1: Ingest Enhancement

**Vibe extraction** — after `describe_image()` completes, a second GPT call (gpt-4o-mini) takes the description and returns:
```json
{ "energy": 0.8, "warmth": 0.9, "density": 0.4, "intimacy": 0.7, "motion": 0.3 }
```
Prompt is tightly constrained — five floats, no prose. Stored as JSONB in `vibe_dimensions`. Cost: ~$0.0001/image.

**UMAP projection** — after each upload, run `umap-learn` over all user image embeddings and write new `map_x`, `map_y` to every row. For libraries <500 images: in-process. Larger: background task. Coordinates normalized to 0–1000. Re-projection only triggers on library change. Coordinates are stable between sessions.

---

## Section 2: Top-Down Map View (`/brain`)

Full-screen canvas. Every image rendered as a thumbnail at its UMAP coordinates.

**Rendering:**
- Pan with drag, zoom with scroll/pinch. Positions are fixed — no physics.
- Thumbnails server-resized to 120px, cached.
- Zoom-out: thumbnails collapse to color dots (warmth + energy → hue/brightness)
- Zoom-in: full thumbnails with glow border (intensity = energy dim)
- Faint traversal path edges drawn between already-visited images
- Dark background + vignette

**Interaction:**
- Tap image → zoom animation into local view centered on that image
- Sequence strip appears at bottom on first selection
- Minimal overlay panel for zoom reset / search — no chrome on canvas itself

---

## Section 3: Local View

Selected image sits large in center. Nearest neighbors (3–8, based on library density) orbit at radius proportional to similarity: `radius = lerp(80, 220, 1 - similarity)`.

**Neighbor arrangement:**
- Angles spread evenly around orbit
- Closer = more similar
- Similarity score badge on hover
- Already-visited images dimmed

**Selection:**
- Tap neighbor → it animates to center, becomes new focal image, previous appends to sequence strip
- Pinch out or back gesture → reverse zoom to map, focused on current position

---

## Section 4: Sequence Strip + Vibe Curve

Persistent strip at screen bottom across both modes. Ordered image tiles. Drag to reorder, long-press to remove.

**Vibe curve:**
Five colored lines (one per dimension) rendering the emotional arc above the strip. Visible once strip has 2+ images. This is the score the composer reads.

**Transition descriptors** — returned by `POST /api/brain/sequence/compose` on each strip change:
```json
{
  "similarity": 0.74,
  "colorShift": "warm_to_cool",
  "moodShift": 0.6,
  "subjectContinuity": true,
  "transitionType": "dissolve",
  "duration": 1.2
}
```

**Transition type matrix:**

| Similarity | Mood delta | Type |
|---|---|---|
| High | Low | `dissolve` |
| High | High | `flash_cut` + particle burst |
| Low | Low | `slow_zoom` + geometric bridge |
| Low | High | `hard_cut` + geometry reset |

---

## Section 5: Composition Layer

Panel alongside sequence strip. Three tabs: Geometry, Sound, Narration. Automatic by default (vibe curve drives all), every parameter manually overridable.

### Geometry
Canvas overlays rendered per-image, animated through transitions:

| Vibe dimension | Drives |
|---|---|
| `energy` | Circle pulse rate |
| `density` | Line density of overlays |
| `warmth` | Color temperature (amber → slate) |
| `intimacy` | Zoom/crop tightness during transition hold |
| `motion` delta | Particle burst intensity on transition |

Subject continuity (`subjectContinuity: true`) → geometric elements echo as ghosts across adjacent frames. This is the "talking to each other" behavior.

### Sound
Tone.js (already in codebase):

| Vibe dimension | Drives |
|---|---|
| `energy` | BPM / pulse rate |
| `warmth` | Chord color (minor ↔ major) |
| `density` | Overtone layering |
| `intimacy` | Reverb wet/dry |
| `motion` delta | Filter sweep speed |

Chord changes triggered at transition points by transition descriptor. Smooth sequence = smooth voice leading. Hard cut = stab chord.

### Narration
Optional. Single GPT call reads full vibe arc → generates short poetic text per image (mood captions, not descriptions). Cormorant Garamond font, subtle overlay. User can edit or delete any segment.

---

## Section 6: Export

Extends `useGlassExport`:

1. Canvas enters render mode (hidden, full resolution)
2. Per image: hold duration (default 3s, scales with `energy`) + transition duration from descriptor
3. `captureStream(30)` → video track
4. Tone.js → `MediaStreamAudioDestination` → audio track
5. `MediaRecorder` combines → MP4 blob → download

Default hold: 3s. A 10-image sequence ≈ 45–60s.

---

## Open Questions / Future
- Bulk ingest from ChatGPT export ZIP — single upload endpoint for batch processing
- Image serving endpoint `GET /api/brain/image/{id}` — currently images stored as base64 in DB, should move to Vercel Blob
- UMAP re-projection strategy for large libraries (>500 images) — background job vs. on-demand
- Sharing / publishing a sequence publicly
