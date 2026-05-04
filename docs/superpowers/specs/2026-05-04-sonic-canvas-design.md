# Data-Driven Sonic Canvas — Design Spec

**Date:** 2026-05-04
**Scope:** `/calibrate/:provider` (ConnectorResultView) — upgrade from decorative physics canvas to data-driven visual + audio experience. Fix genre bug and LLM error surfacing.

---

## Overview

The ConnectorResultView hero canvas currently shows a generic particle system colored by provider hex. The `connectorConfig.physics` mapping already defines how Spotify fields should drive physics params — but it's never consumed. This spec upgrades the canvas to a living data portrait (Matter.js) with a personalized rhythmic layer (Tone.js), and fixes three bugs: empty genres, silent Read Analysis failures, and missing Cross Correlations.

---

## 1. Matter.js Data-Driven Physics

### Parameter Mapping

| Spotify Field | Physics Param | Effect |
|---|---|---|
| `audio_avg.energy` (0-1) | particleSpeed | Base velocity multiplier. 0.2 = drifting, 0.9 = frenetic |
| `audio_avg.valence` (0-1) | colorTemp | Color palette shift. Low = cool blues/purples, High = warm ambers/pinks |
| `audio_avg.tempo` (60-200) | pulseRate | Orb size oscillation frequency. Normalized to 0.5-2Hz |
| `genres.length` (0-8) | particleCount | Scaled: `80 + (count * 20)`. 0 genres = 80, 8 = 240 |
| `audio_avg.acousticness` (0-1) | sizeVariance | High = larger size range (organic), low = uniform (synthetic) |

### Valence Color Palette

- `< 0.3`: Deep blues, teals (#1a5276, #2471a3, #48c9b0)
- `0.3-0.5`: Purples, magentas (#7d3c98, #a569bd, #c39bd3)
- `0.5-0.7`: Provider color (e.g. Spotify green) with warm accents
- `> 0.7`: Ambers, golds, warm pinks (#f39c12, #e74c3c, #f1948a)

### Implementation

New composable `useDataDrivenPhysics(canvasRef, profile, physicsCfg)`:
- Reads profile data and the `connectorConfig.physics` field mapping
- Resolves each mapped field via `resolveField()`
- Translates values into `useCosmicPhysics` options (orbDefs with valence-driven colors, particleCount, clearAlpha scaled to energy)
- Wraps `useCosmicPhysics` — does not modify it

---

## 2. Tone.js Rhythmic Layer

### Parameter Mapping

| Spotify Field | Audio Param | Effect |
|---|---|---|
| `audio_avg.tempo` | BPM | Direct, clamped 60-180. Drives `Tone.Transport.bpm` |
| `audio_avg.energy` (0-1) | Pattern density | Low = sparse kick-only, High = full kit |
| `audio_avg.valence` (0-1) | Scale/harmony | < 0.4 = minor pentatonic, 0.4-0.6 = dorian, > 0.6 = major |
| `audio_avg.acousticness` (0-1) | Filter warmth | Lowpass cutoff: high acousticness = 800Hz (warm), low = 8kHz (bright) |
| `audio_avg.danceability` (0-1) | Swing | `Tone.Transport.swing` amount (0 = straight, 0.6 = max groove) |

### Sound Sources (Tone.js built-in, no samples)

- **Kick**: `MembraneSynth` — pitched low, short decay
- **Hat**: `NoiseSynth` with bandpass filter — short envelope, high freq
- **Snare**: `NoiseSynth` + `MembraneSynth` layered — mid freq burst
- **Pad**: `PolySynth(FMSynth)` — sustained chord, valence picks voicing
- **Bass**: `MonoSynth` — root note following pad chord, eighth-note pattern

### Energy-Driven Pattern Density

| Energy Range | Active Voices |
|---|---|
| `< 0.3` | Kick only, every 2 beats. Sparse, meditative. |
| `0.3-0.5` | Kick + hat. Basic pulse. |
| `0.5-0.7` | Kick + hat + bass. Groove emerges. |
| `> 0.7` | Full kit + bass + occasional snare fills. |

Pad always plays (sustained, quiet) to establish tonality.

### User Controls

- **Mute/unmute toggle** — bottom-right corner, starts muted (no autoplay)
- **Volume slider** — small, minimal, appears near mute toggle
- `Tone.start()` on first unmute click (browser autoplay policy)
- `Tone.Transport.stop()` + full dispose on component unmount

### Implementation

New composable `useSignalSynth(profile)`:
- Creates all synth voices on init
- Builds Tone.js `Sequence` / `Loop` patterns based on energy level
- Exposes: `start()`, `stop()`, `setVolume(n)`, `isMuted`, `setPan(n)`, `spikeResonance()`
- All synths routed through a shared master filter (acousticness) and gain (volume)

---

## 3. Interactivity — Mouse-Audio Coupling

### Mouse to Audio

- **Hover position X** → stereo pan of pad synth. Left edge = -1, right edge = +1. Subtle spatial movement.
- **Mouse velocity** → filter resonance spike. Fast movement briefly opens filter Q ("wah" sweep), decays back. Makes canvas feel responsive.
- **Click** → one-shot percussive hit (pitched `MembraneSynth`, random note from active scale). Visual: spawns burst of 8-12 particles from click point.

### Scroll to Volume

- As user scrolls past hero canvas, audio volume fades proportionally to `canvasOpacity` (existing parallax logic)
- At narrative section depth, audio is ~20% — ambient background, not competing
- Scrolling back up restores volume

### Mouse to Physics

- Existing `enableMouseInteract: true` / `mouseAttractForce` — no changes needed
- Data-driven speed/size params are base values; mouse attraction overlays on top

No new UI chrome beyond the mute toggle and volume slider. Interactivity is discovered, not instructed.

---

## 4. Bug Fix: Empty Genres

### Problem

`_distill_profile()` only pulls genres from `artists[:5].genres`. Spotify increasingly returns empty genre arrays on artist objects.

### Fix

In `_distill_profile` (and the callback/sync flows that call it):

1. Keep existing: pull genres from top artists response
2. Extract unique artist IDs from top tracks that aren't already in the top artists set
3. Batch-fetch those additional artists via `GET /v1/artists?ids=...` (up to 50 per call)
4. Merge their genres into the pool, same dedup logic
5. If still empty, pull genres from recently played tracks' artists as last resort

Changes limited to `server/app/spotify/router.py`:
- `_distill_profile()` accepts a new `extra_artists` param
- Callback and sync flows fetch the additional artists before calling distill

No LLM fallback. Pure data sourcing.

---

## 5. Bug Fix: LLM Error Surfacing

### Problem

Read Analysis and Cross Correlations silently return empty/generic messages when LLM is unconfigured or fails.

### Backend Fix

- Add `GET /api/connectors/llm-status` endpoint (no auth): returns `{ configured: bool, provider: string, model: string }` — no keys exposed
- Correlations endpoint: log actual error before returning `[]`

### Frontend Fix

ConnectorResultView checks LLM status on mount via existing `/api/connectors/available` (returns `{ llm: bool }`):

**Read Analysis error messages:**
- `llm: false` → "Narrative engine offline — LLM not configured on the server."
- `llm: true` + 502 → "Narrative engine returned an error — try again in a moment."
- `llm: true` + 404 → "No data captured yet — try reconnecting this provider."

**Correlations error messages:**
- `llm: false` → "Cross-signal analysis requires an LLM key on the server."
- `llm: true` + empty result → "Connect more services to see correlations." (existing)
- Distinguish fewer than 2 providers from LLM failure

---

## 6. File Map

### New Files

| File | Purpose |
|---|---|
| `src/composables/useDataDrivenPhysics.ts` | Wraps `useCosmicPhysics`, translates profile → physics params via connectorConfig mapping |
| `src/composables/useSignalSynth.ts` | Tone.js rhythmic engine: synthesis, patterns, mouse-audio coupling, volume/mute |

### Modified Files

| File | Changes |
|---|---|
| `src/views/ConnectorResultView.vue` | Replace `hexToOrbDefs` + raw `useCosmicPhysics` with `useDataDrivenPhysics`. Add `useSignalSynth`. Mute toggle + volume slider. Mouse→synth wiring. Scroll→volume fade. Better error messages for narrative + correlations. |
| `server/app/spotify/router.py` | `_distill_profile`: accept extra artists, merge genres. Callback + sync: fetch track artists before distilling. |
| `server/app/connectors/router.py` | Add `GET /connectors/llm-status`. Log correlation errors. |

### Untouched

- `src/composables/useCosmicPhysics.ts` — consumed as-is, wrapped
- `src/composables/useSpotifyPhysics.ts` — separate `/spotify` page, not in scope
- `src/views/OauthView.vue` — calibrate hub, unchanged
- `src/config/connectorConfig.ts` — physics mapping already correct
- Backend `/analyze` endpoints — logic is fine, frontend handles errors better

### Dependencies

- `tone` added via npm — Tone.js for audio synthesis
- Matter.js unchanged (CDN)

---

## 7. What This Does NOT Include

- Changes to the `/spotify` visualization page (SpotifyView.vue) — separate scope
- Audio samples or external sound files — all Tone.js built-in synthesis
- New backend routes beyond `llm-status` diagnostic
- LLM-based genre inference — pure data sourcing only
- Changes to the Oracle synthesis or matching pipeline
