# Data-Driven Sonic Canvas Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade ConnectorResultView's decorative canvas into a data-driven Matter.js + Tone.js experience, fix empty genres, and surface LLM errors.

**Architecture:** Two new composables (`useDataDrivenPhysics`, `useSignalSynth`) wrap existing infrastructure. `useDataDrivenPhysics` translates profile data into `useCosmicPhysics` options via the existing `connectorConfig.physics` mapping. `useSignalSynth` creates a Tone.js rhythmic loop driven by audio metrics. ConnectorResultView wires both together with mouse/scroll interactivity. Backend genre fix supplements artist genres with track-artist genres. LLM error surfacing adds a diagnostic endpoint and better frontend messaging.

**Tech Stack:** Vue 3 + TypeScript, Matter.js (CDN), Tone.js v15 (npm, already installed), FastAPI (Python)

**Spec:** `docs/superpowers/specs/2026-05-04-sonic-canvas-design.md`

---

### Task 1: Genre Bug Fix (Backend)

**Files:**
- Modify: `server/app/spotify/router.py:65-151` (sync), `server/app/spotify/router.py:177-287` (callback), `server/app/spotify/router.py:322-356` (_distill_profile)

- [ ] **Step 1: Update `_distill_profile` to accept extra artists**

In `server/app/spotify/router.py`, replace `_distill_profile`:

```python
def _distill_profile(artists: list[dict], features: list[dict], tracks: list[dict] | None = None, extra_artists: list[dict] | None = None) -> dict:
    """Reduce raw Spotify data to the essentials we care about."""
    top_artist_names = [a["name"] for a in artists[:5]]
    genres: list[str] = []
    for a in artists[:5]:
        genres.extend(a.get("genres", []))

    # Supplement with genres from track artists (Spotify often has genres
    # on track-level artist objects when top-artists are empty)
    if extra_artists:
        for a in extra_artists:
            genres.extend(a.get("genres", []))

    # Deduplicate while preserving order
    seen: set = set()
    unique_genres = [g for g in genres if not (g in seen or seen.add(g))][:8]  # type: ignore[func-returns-value]

    avg: dict[str, float] = {}
    keys = ["valence", "danceability", "energy", "acousticness", "instrumentalness", "tempo"]
    if features:
        for k in keys:
            vals = [f[k] for f in features if k in f]
            avg[k] = round(sum(vals) / len(vals), 3) if vals else 0.0

    # Fallback: if audio-features returned nothing (deprecated API), infer from genres + track popularity
    if not avg or not any(avg.get(k) for k in keys):
        avg["valence"] = _infer_valence_from_genres(unique_genres)
        # Use average track popularity (0-100) normalized to 0-1 as energy proxy
        if tracks:
            pops = [t.get("popularity", 50) for t in tracks]
            avg["energy"] = round(sum(pops) / len(pops) / 100, 3) if pops else 0.5
        else:
            avg["energy"] = 0.5
        avg["danceability"] = round((avg["valence"] + avg["energy"]) / 2, 3)
        avg["acousticness"] = round(1 - avg["energy"], 3)
        avg["tempo"] = 120.0

    return {
        "top_artists": top_artist_names,
        "genres": unique_genres,
        "audio_avg": avg,
    }
```

- [ ] **Step 2: Add helper to fetch extra artist genres from track artists**

Add this function above `_distill_profile` in `server/app/spotify/router.py`:

```python
async def _fetch_track_artist_genres(
    client: httpx.AsyncClient,
    headers: dict[str, str],
    tracks_data: list[dict],
    top_artist_ids: set[str],
) -> list[dict]:
    """Fetch full artist objects for artists appearing in tracks but not in top artists.

    Spotify often has genre data on these artist objects even when top-artists
    returns empty genres arrays.
    """
    # Collect unique artist IDs from tracks that aren't already in top artists
    extra_ids: list[str] = []
    seen: set[str] = set()
    for track in tracks_data:
        for artist in track.get("artists", []):
            aid = artist.get("id", "")
            if aid and aid not in top_artist_ids and aid not in seen:
                seen.add(aid)
                extra_ids.append(aid)

    if not extra_ids:
        return []

    # Spotify batch endpoint accepts up to 50 IDs
    extra_ids = extra_ids[:50]
    resp = await client.get(
        f"{_SPOTIFY_API_BASE}/artists",
        headers=headers,
        params={"ids": ",".join(extra_ids)},
    )
    if resp.status_code != 200:
        return []
    return resp.json().get("artists", [])
```

- [ ] **Step 3: Wire extra artist fetch into callback flow**

In `server/app/spotify/router.py`, in the `spotify_callback` function, after the `tracks_data` assignment (around line 245) and before `# 5. Distill the audio profile`, add the extra artist fetch:

Replace the line:
```python
    # 5. Distill the audio profile
    spotify_profile = _distill_profile(artists_data, audio_features, tracks_data)
```

With:
```python
        # 4c. Fetch extra artist genres from track artists
        top_artist_ids = {a["id"] for a in artists_data if "id" in a}
        extra_artists = await _fetch_track_artist_genres(
            client, headers, tracks_data, top_artist_ids,
        )

    # 5. Distill the audio profile
    spotify_profile = _distill_profile(artists_data, audio_features, tracks_data, extra_artists)
```

Note: the `extra_artists` fetch must be inside the `async with httpx.AsyncClient` block, so move it before the block closes. The `_distill_profile` call stays outside.

- [ ] **Step 4: Wire extra artist fetch into sync flow**

In `server/app/spotify/router.py`, in the `spotify_sync` function, after the audio features fetch (around line 143) and before the client block closes, add:

```python
        # Fetch extra artist genres from track artists
        top_artist_ids = {a["id"] for a in artists_data if "id" in a}
        extra_artists = await _fetch_track_artist_genres(
            client, headers, tracks_data, top_artist_ids,
        )

    spotify_profile = _distill_profile(artists_data, audio_features, tracks_data, extra_artists)
```

- [ ] **Step 5: Verify the build hasn't broken**

Run: `cd server && python -c "from app.spotify.router import router; print('OK')"`
Expected: `OK`

- [ ] **Step 6: Commit**

```bash
git add server/app/spotify/router.py
git commit -m "Fix empty genres by supplementing with track-artist genre data"
```

---

### Task 2: LLM Error Surfacing (Backend + Frontend)

**Files:**
- Modify: `server/app/connectors/router.py` (add llm-status endpoint, add logging)
- Modify: `src/views/ConnectorResultView.vue:429-463` (better error messages)

- [ ] **Step 1: Add `llm-status` endpoint**

In `server/app/connectors/router.py`, add this endpoint after the `get_available_connectors` function (after line 71):

```python
@router.get("/llm-status")
async def get_llm_status():
    """Diagnostic endpoint — returns LLM configuration state (no keys exposed)."""
    settings = get_settings()
    provider = (settings.llm_provider or "openai").lower()
    return {
        "configured": llm_configured(),
        "provider": provider,
        "model": settings.llm_model or _PROVIDERS.get(provider, {}).get("default_model", "unknown"),
    }
```

Also add the import for `_PROVIDERS` at the top of the file. Actually, `_PROVIDERS` is private to `chat.py`. Instead, just return the provider name and model from settings directly:

```python
@router.get("/llm-status")
async def get_llm_status():
    """Diagnostic endpoint — returns LLM configuration state (no keys exposed)."""
    settings = get_settings()
    provider = (settings.llm_provider or "openai").lower()
    return {
        "configured": llm_configured(),
        "provider": provider,
        "model": settings.llm_model or ("gpt-4o-mini" if provider == "openai" else "openai/gpt-4o-mini"),
    }
```

- [ ] **Step 2: Add error logging to correlations endpoint**

In `server/app/connectors/router.py`, add `import logging` at the top and add a logger:

```python
import logging

logger = logging.getLogger(__name__)
```

Then in `_find_correlations`, update the exception handler (around line 168):

```python
    try:
        content = await chat_completion(prompt, max_tokens=1200)
    except HTTPException as exc:
        logger.warning("Correlations LLM call failed for %s: %s", target_provider, exc.detail)
        return []
```

And update the JSON parse error handler (around line 182):

```python
    except (json.JSONDecodeError, KeyError, IndexError) as exc:
        logger.warning("Failed to parse correlations LLM response: %s", exc)
        return []
```

- [ ] **Step 3: Update frontend error messages for narrative**

In `src/views/ConnectorResultView.vue`, add LLM availability check. Add a new ref and fetch it on mount:

After the `correlationsLoading` ref (line 290), add:

```typescript
const llmAvailable = ref(true)
```

In `onMounted`, before `fetchProfile()` (line 487), add:

```typescript
  // Check LLM availability
  try {
    const avail = await apiFetch<{ providers: Record<string, boolean>; llm: boolean }>('/api/connectors/available')
    llmAvailable.value = avail.llm
  } catch { /* assume available */ }
```

Then update `fetchNarrative` to use `llmAvailable`:

```typescript
async function fetchNarrative() {
  if (!provider.value || !cfg.value) return
  if (!llmAvailable.value) {
    narrativeError.value = true
    narrativeErrorMsg.value = 'Narrative engine offline — LLM not configured on the server.'
    return
  }
  narrativeLoading.value = true
  narrativeError.value = false
  try {
    const data = await apiFetch<{ narrative: string }>(analyzeEndpoint(provider.value))
    narrative.value = data.narrative || ''
  } catch (e: any) {
    narrativeError.value = true
    const msg = String(e?.message || '')
    if (msg.includes('404')) {
      narrativeErrorMsg.value = 'No data captured yet — try reconnecting this provider.'
    } else if (msg.includes('503')) {
      narrativeErrorMsg.value = 'Narrative engine offline — LLM not configured on the server.'
    } else if (msg.includes('502')) {
      narrativeErrorMsg.value = 'Narrative engine returned an error — try again in a moment.'
    } else {
      narrativeErrorMsg.value = 'Analysis not available yet.'
    }
  }
  narrativeLoading.value = false
}
```

- [ ] **Step 4: Update frontend error messages for correlations**

Update `fetchCorrelations` to use `llmAvailable`:

```typescript
async function fetchCorrelations() {
  if (!provider.value) return
  if (!llmAvailable.value) {
    correlations.value = []
    return
  }
  correlationsLoading.value = true
  try {
    const data = await apiFetch<Correlation[]>(
      `/api/connectors/correlations?provider=${provider.value}`
    )
    correlations.value = Array.isArray(data) ? data : []
  } catch {
    correlations.value = []
  }
  correlationsLoading.value = false
}
```

Update the empty-state message in the template (line 159-161) to be context-aware:

```html
      <div v-else-if="!correlations.length" class="text-center py-12">
        <p class="text-gray-600 font-mono text-sm">
          {{ !llmAvailable ? 'Cross-signal analysis requires an LLM key on the server.' : 'Connect more services to see correlations.' }}
        </p>
      </div>
```

- [ ] **Step 5: Verify build**

Run: `npm run type-check`
Expected: No errors

- [ ] **Step 6: Commit**

```bash
git add server/app/connectors/router.py src/views/ConnectorResultView.vue
git commit -m "Surface LLM status in narrative and correlation error messages"
```

---

### Task 3: `useDataDrivenPhysics` Composable

**Files:**
- Create: `src/composables/useDataDrivenPhysics.ts`
- Test: `src/__tests__/composables/useDataDrivenPhysics.test.ts`

- [ ] **Step 1: Write the test**

Create `src/__tests__/composables/useDataDrivenPhysics.test.ts`:

```typescript
import { describe, it, expect } from 'vitest'
import { buildPhysicsOptions, valenceToOrbDefs } from '@/composables/useDataDrivenPhysics'

describe('buildPhysicsOptions', () => {
  const profile = {
    top_artists: ['Artist A', 'Artist B'],
    genres: ['electronic', 'ambient', 'indie'],
    audio_avg: {
      energy: 0.7,
      valence: 0.45,
      danceability: 0.6,
      acousticness: 0.3,
      tempo: 128,
    },
  }
  const physicsCfg = {
    particleSpeed: 'audio_avg.energy',
    colorTemp: 'audio_avg.valence',
    particleCount: 'genres.length',
    pulseRate: 'audio_avg.tempo',
    sizeVariance: 'audio_avg.acousticness',
  }

  it('maps energy to clearAlpha (higher energy = crisper trail)', () => {
    const opts = buildPhysicsOptions(profile, physicsCfg, '#1db954')
    // energy 0.7 → clearAlpha should be higher than base
    expect(opts.clearAlpha).toBeGreaterThan(0.06)
    expect(opts.clearAlpha).toBeLessThan(0.2)
  })

  it('maps genre count to particleCount', () => {
    const opts = buildPhysicsOptions(profile, physicsCfg, '#1db954')
    // 3 genres → 80 + 3*20 = 140
    expect(opts.particleCount).toBe(140)
  })

  it('maps energy to mouseAttractForce', () => {
    const opts = buildPhysicsOptions(profile, physicsCfg, '#1db954')
    // energy 0.7 → 0.25 + 0.7*0.6 = 0.67
    expect(opts.mouseAttractForce).toBeCloseTo(0.67, 1)
  })

  it('falls back to defaults when profile is empty', () => {
    const empty = { top_artists: [], genres: [], audio_avg: {} }
    const opts = buildPhysicsOptions(empty, physicsCfg, '#1db954')
    expect(opts.particleCount).toBe(80)
    expect(opts.orbDefs.length).toBeGreaterThan(0)
  })
})

describe('valenceToOrbDefs', () => {
  it('returns cool colors for low valence', () => {
    const defs = valenceToOrbDefs(0.2, '#1db954')
    // Low valence → blue/teal tones: high blue channel
    expect(defs[0].b).toBeGreaterThan(defs[0].r)
  })

  it('returns warm colors for high valence', () => {
    const defs = valenceToOrbDefs(0.8, '#1db954')
    // High valence → amber/warm: high red channel
    expect(defs[0].r).toBeGreaterThan(defs[0].b)
  })

  it('uses provider color for mid valence', () => {
    const defs = valenceToOrbDefs(0.55, '#1db954')
    // Mid valence → provider green: green channel dominant
    expect(defs[0].g).toBeGreaterThan(100)
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run src/__tests__/composables/useDataDrivenPhysics.test.ts`
Expected: FAIL — module not found

- [ ] **Step 3: Write the composable**

Create `src/composables/useDataDrivenPhysics.ts`:

```typescript
import { type Ref } from 'vue'
import { useCosmicPhysics, type OrbDef, type CosmicConfig } from './useCosmicPhysics'
import { resolveField } from '@/config/connectorConfig'

// ── Valence → color palette ────────────────────────────────────────────────

const COOL_PALETTE: OrbDef[] = [
  { r: 26, g: 82, b: 118 },   // deep blue
  { r: 36, g: 113, b: 163 },  // steel blue
  { r: 72, g: 201, b: 176 },  // teal
  { r: 46, g: 134, b: 193 },  // sky
]

const PURPLE_PALETTE: OrbDef[] = [
  { r: 125, g: 60, b: 152 },  // purple
  { r: 165, g: 105, b: 189 }, // magenta
  { r: 195, g: 155, b: 211 }, // lavender
  { r: 142, g: 68, b: 173 },  // violet
]

const WARM_PALETTE: OrbDef[] = [
  { r: 243, g: 156, b: 18 },  // amber
  { r: 231, g: 76, b: 60 },   // coral
  { r: 241, g: 148, b: 138 }, // warm pink
  { r: 245, g: 176, b: 65 },  // gold
]

function hexToRgb(hex: string): OrbDef {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return { r, g, b }
}

function providerPalette(hex: string): OrbDef[] {
  const base = hexToRgb(hex)
  return [
    base,
    { r: Math.max(0, base.r - 40), g: Math.max(0, base.g - 20), b: Math.min(255, base.b + 30) },
    { r: Math.min(255, base.r + 30), g: Math.max(0, base.g - 30), b: Math.max(0, base.b - 20) },
    { r: Math.max(0, base.r - 20), g: Math.min(255, base.g + 40), b: Math.min(255, base.b + 20) },
  ]
}

export function valenceToOrbDefs(valence: number, providerHex: string): OrbDef[] {
  if (valence < 0.3) return COOL_PALETTE
  if (valence < 0.5) return PURPLE_PALETTE
  if (valence <= 0.7) return providerPalette(providerHex)
  return WARM_PALETTE
}

// ── Build physics options from profile data ────────────────────────────────

interface PhysicsFieldMap {
  particleSpeed: string
  colorTemp: string
  particleCount: string
  pulseRate: string
  sizeVariance?: string
}

export function buildPhysicsOptions(
  profile: Record<string, unknown>,
  physicsCfg: PhysicsFieldMap,
  providerHex: string,
): Required<CosmicConfig> {
  const energy = Number(resolveField(profile, physicsCfg.particleSpeed) ?? 0.5)
  const valence = Number(resolveField(profile, physicsCfg.colorTemp) ?? 0.5)
  const genreCount = Number(resolveField(profile, physicsCfg.particleCount) ?? 0)
  const tempo = Number(resolveField(profile, physicsCfg.pulseRate) ?? 120)
  const acousticness = Number(resolveField(profile, physicsCfg.sizeVariance ?? '') ?? 0.5)

  // Normalize tempo to 0-1 range (60-200 BPM)
  const normTempo = Math.min(1, Math.max(0, (tempo - 60) / 140))

  return {
    orbDefs: valenceToOrbDefs(valence, providerHex),
    particleCount: 80 + Math.round(genreCount * 20),
    starCount: 120,
    clearAlpha: 0.055 + energy * 0.06 + normTempo * 0.02,
    enableKeyboard: false,
    enableMouseInteract: true,
    mouseAttractForce: 0.25 + energy * 0.6,
  }
}

// ── Composable ─────────────────────────────────────────────────────────────

export function useDataDrivenPhysics(
  canvasRef: Ref<HTMLCanvasElement | undefined>,
  profile: Record<string, unknown> | null,
  physicsCfg: PhysicsFieldMap,
  providerHex: string,
) {
  const options = profile
    ? buildPhysicsOptions(profile, physicsCfg, providerHex)
    : {
        orbDefs: providerPalette(providerHex),
        particleCount: 180,
        starCount: 120,
        clearAlpha: 0.08,
        enableKeyboard: false,
        enableMouseInteract: true,
        mouseAttractForce: 0.6,
      }

  const cosmic = useCosmicPhysics(canvasRef, options)

  return {
    ...cosmic,
    /** The resolved valence for external consumers (e.g. audio layer) */
    valence: profile ? Number(resolveField(profile, physicsCfg.colorTemp) ?? 0.5) : 0.5,
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npx vitest run src/__tests__/composables/useDataDrivenPhysics.test.ts`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/composables/useDataDrivenPhysics.ts src/__tests__/composables/useDataDrivenPhysics.test.ts
git commit -m "Add useDataDrivenPhysics composable with valence color palettes"
```

---

### Task 4: `useSignalSynth` Composable

**Files:**
- Create: `src/composables/useSignalSynth.ts`
- Test: `src/__tests__/composables/useSignalSynth.test.ts`

- [ ] **Step 1: Write the test**

Create `src/__tests__/composables/useSignalSynth.test.ts`:

```typescript
import { describe, it, expect } from 'vitest'
import { buildSynthConfig, pickChord } from '@/composables/useSignalSynth'

describe('buildSynthConfig', () => {
  it('clamps BPM to 60-180 range', () => {
    const cfg = buildSynthConfig({ tempo: 30, energy: 0.5, valence: 0.5, danceability: 0.5, acousticness: 0.5 })
    expect(cfg.bpm).toBe(60)
    const cfg2 = buildSynthConfig({ tempo: 250, energy: 0.5, valence: 0.5, danceability: 0.5, acousticness: 0.5 })
    expect(cfg2.bpm).toBe(180)
  })

  it('maps energy to active voices', () => {
    const low = buildSynthConfig({ tempo: 120, energy: 0.2, valence: 0.5, danceability: 0.5, acousticness: 0.5 })
    expect(low.voices).toEqual(['kick'])

    const mid = buildSynthConfig({ tempo: 120, energy: 0.4, valence: 0.5, danceability: 0.5, acousticness: 0.5 })
    expect(mid.voices).toEqual(['kick', 'hat'])

    const high = buildSynthConfig({ tempo: 120, energy: 0.6, valence: 0.5, danceability: 0.5, acousticness: 0.5 })
    expect(high.voices).toEqual(['kick', 'hat', 'bass'])

    const full = buildSynthConfig({ tempo: 120, energy: 0.8, valence: 0.5, danceability: 0.5, acousticness: 0.5 })
    expect(full.voices).toEqual(['kick', 'hat', 'bass', 'snare'])
  })

  it('maps acousticness to filter cutoff', () => {
    const warm = buildSynthConfig({ tempo: 120, energy: 0.5, valence: 0.5, danceability: 0.5, acousticness: 0.9 })
    expect(warm.filterCutoff).toBeLessThan(1500)

    const bright = buildSynthConfig({ tempo: 120, energy: 0.5, valence: 0.5, danceability: 0.5, acousticness: 0.1 })
    expect(bright.filterCutoff).toBeGreaterThan(5000)
  })

  it('maps danceability to swing', () => {
    const straight = buildSynthConfig({ tempo: 120, energy: 0.5, valence: 0.5, danceability: 0.0, acousticness: 0.5 })
    expect(straight.swing).toBe(0)

    const groovy = buildSynthConfig({ tempo: 120, energy: 0.5, valence: 0.5, danceability: 1.0, acousticness: 0.5 })
    expect(groovy.swing).toBeCloseTo(0.6, 1)
  })
})

describe('pickChord', () => {
  it('returns minor pentatonic notes for low valence', () => {
    const chord = pickChord(0.2)
    // Minor pentatonic from C: C Eb F G Bb
    expect(chord).toContain('C4')
    expect(chord).toContain('Eb4')
  })

  it('returns major notes for high valence', () => {
    const chord = pickChord(0.8)
    // Major: C E G B
    expect(chord).toContain('C4')
    expect(chord).toContain('E4')
  })

  it('returns dorian notes for mid valence', () => {
    const chord = pickChord(0.5)
    // Dorian: C D Eb G A
    expect(chord).toContain('C4')
    expect(chord).toContain('Eb4')
    expect(chord).toContain('G4')
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run src/__tests__/composables/useSignalSynth.test.ts`
Expected: FAIL — module not found

- [ ] **Step 3: Write the composable**

Create `src/composables/useSignalSynth.ts`:

```typescript
import { ref } from 'vue'
import * as Tone from 'tone'

// ── Types ──────────────────────────────────────────────────────────────────

export interface AudioMetrics {
  tempo: number
  energy: number
  valence: number
  danceability: number
  acousticness: number
}

export interface SynthConfig {
  bpm: number
  voices: string[]
  filterCutoff: number
  swing: number
  chord: string[]
  bassNote: string
}

// ── Pure config builders (testable without Tone.js) ────────────────────────

export function buildSynthConfig(metrics: AudioMetrics): SynthConfig {
  const bpm = Math.max(60, Math.min(180, Math.round(metrics.tempo)))

  let voices: string[]
  if (metrics.energy < 0.3) {
    voices = ['kick']
  } else if (metrics.energy < 0.5) {
    voices = ['kick', 'hat']
  } else if (metrics.energy < 0.7) {
    voices = ['kick', 'hat', 'bass']
  } else {
    voices = ['kick', 'hat', 'bass', 'snare']
  }

  // acousticness 0→8000Hz, 1→800Hz
  const filterCutoff = 800 + (1 - metrics.acousticness) * 7200

  const swing = metrics.danceability * 0.6

  const chord = pickChord(metrics.valence)
  const bassNote = 'C2'

  return { bpm, voices, filterCutoff, swing, chord, bassNote }
}

export function pickChord(valence: number): string[] {
  if (valence < 0.4) {
    // Minor pentatonic: C Eb F G Bb
    return ['C4', 'Eb4', 'G4', 'Bb4']
  } else if (valence <= 0.6) {
    // Dorian: Cm7 voicing — C Eb G A
    return ['C4', 'Eb4', 'G4', 'A4']
  } else {
    // Major: Cmaj7 — C E G B
    return ['C4', 'E4', 'G4', 'B4']
  }
}

// Scale notes for one-shot hits
function scaleNotes(valence: number): string[] {
  if (valence < 0.4) return ['C5', 'Eb5', 'F5', 'G5', 'Bb5']
  if (valence <= 0.6) return ['C5', 'D5', 'Eb5', 'G5', 'A5']
  return ['C5', 'D5', 'E5', 'G5', 'A5', 'B5']
}

// ── Composable ─────────────────────────────────────────────────────────────

export function useSignalSynth(metrics: AudioMetrics) {
  const isMuted = ref(true)
  const isStarted = ref(false)
  const config = buildSynthConfig(metrics)
  const notes = scaleNotes(metrics.valence)

  // Synth instances (created lazily on start)
  let masterFilter: Tone.Filter | null = null
  let masterGain: Tone.Gain | null = null
  let panner: Tone.Panner | null = null
  let kick: Tone.MembraneSynth | null = null
  let hat: Tone.NoiseSynth | null = null
  let snare: { noise: Tone.NoiseSynth; membrane: Tone.MembraneSynth } | null = null
  let pad: Tone.PolySynth | null = null
  let bass: Tone.MonoSynth | null = null
  let hitSynth: Tone.MembraneSynth | null = null
  let loops: Tone.Loop[] = []

  function createSynths() {
    // Master chain: synths → panner → filter → gain → destination
    masterGain = new Tone.Gain(0.35).toDestination()
    masterFilter = new Tone.Filter(config.filterCutoff, 'lowpass', -12).connect(masterGain)
    panner = new Tone.Panner(0).connect(masterFilter)

    // Kick
    kick = new Tone.MembraneSynth({
      pitchDecay: 0.05,
      octaves: 6,
      oscillator: { type: 'sine' },
      envelope: { attack: 0.001, decay: 0.3, sustain: 0, release: 0.1 },
    }).connect(masterFilter)
    kick.volume.value = -6

    // Hat
    hat = new Tone.NoiseSynth({
      noise: { type: 'white' },
      envelope: { attack: 0.001, decay: 0.08, sustain: 0, release: 0.01 },
    }).connect(masterFilter)
    hat.volume.value = -18

    // Snare
    const snareNoise = new Tone.NoiseSynth({
      noise: { type: 'pink' },
      envelope: { attack: 0.001, decay: 0.15, sustain: 0, release: 0.05 },
    }).connect(masterFilter)
    snareNoise.volume.value = -12
    const snareMembrane = new Tone.MembraneSynth({
      pitchDecay: 0.02,
      octaves: 4,
      envelope: { attack: 0.001, decay: 0.12, sustain: 0, release: 0.05 },
    }).connect(masterFilter)
    snareMembrane.volume.value = -14
    snare = { noise: snareNoise, membrane: snareMembrane }

    // Pad — sustained chord, quiet
    pad = new Tone.PolySynth(Tone.FMSynth, {
      harmonicity: 2,
      modulationIndex: 1.5,
      envelope: { attack: 0.8, decay: 1.5, sustain: 0.6, release: 2 },
    }).connect(panner!)
    pad.volume.value = -22

    // Bass
    bass = new Tone.MonoSynth({
      oscillator: { type: 'triangle' },
      envelope: { attack: 0.01, decay: 0.2, sustain: 0.3, release: 0.1 },
      filterEnvelope: { attack: 0.01, decay: 0.1, sustain: 0.5, release: 0.2, baseFrequency: 200, octaves: 2 },
    }).connect(masterFilter)
    bass.volume.value = -10

    // One-shot hit synth for click interaction
    hitSynth = new Tone.MembraneSynth({
      pitchDecay: 0.08,
      octaves: 4,
      envelope: { attack: 0.001, decay: 0.25, sustain: 0, release: 0.15 },
    }).connect(masterFilter)
    hitSynth.volume.value = -8
  }

  function createPatterns() {
    const v = config.voices

    // Kick: every beat (or every 2 beats if sparse)
    if (v.includes('kick')) {
      const interval = metrics.energy < 0.3 ? '2n' : '4n'
      loops.push(new Tone.Loop((time) => {
        kick?.triggerAttackRelease('C1', '8n', time)
      }, interval))
    }

    // Hat: eighth notes
    if (v.includes('hat')) {
      loops.push(new Tone.Loop((time) => {
        hat?.triggerAttackRelease('16n', time)
      }, '8n'))
    }

    // Bass: eighth notes on root
    if (v.includes('bass')) {
      loops.push(new Tone.Loop((time) => {
        bass?.triggerAttackRelease(config.bassNote, '8n', time)
      }, '8n'))
    }

    // Snare: beats 2 and 4
    if (v.includes('snare')) {
      let beatCount = 0
      loops.push(new Tone.Loop((time) => {
        beatCount++
        if (beatCount % 2 === 0) {
          snare?.noise.triggerAttackRelease('16n', time)
          snare?.membrane.triggerAttackRelease('E2', '16n', time)
        }
      }, '4n'))
    }

    // Pad: sustained chord, re-trigger every 2 bars
    loops.push(new Tone.Loop((time) => {
      pad?.triggerAttackRelease(config.chord, '1m', time)
    }, '2m'))

    // Start all loops
    for (const loop of loops) {
      loop.start(0)
    }
  }

  async function start() {
    if (isStarted.value) {
      Tone.getTransport().start()
      isMuted.value = false
      return
    }

    await Tone.start()
    createSynths()

    Tone.getTransport().bpm.value = config.bpm
    Tone.getTransport().swing = config.swing

    createPatterns()
    Tone.getTransport().start()

    isStarted.value = true
    isMuted.value = false
  }

  function stop() {
    Tone.getTransport().pause()
    isMuted.value = true
  }

  function toggle() {
    if (isMuted.value) {
      start()
    } else {
      stop()
    }
  }

  function setVolume(normalized: number) {
    if (masterGain) {
      masterGain.gain.value = Math.max(0, Math.min(1, normalized)) * 0.5
    }
  }

  function setPan(value: number) {
    if (panner) {
      panner.pan.value = Math.max(-1, Math.min(1, value))
    }
  }

  function spikeResonance(intensity: number = 0.5) {
    if (masterFilter) {
      const baseQ = 1
      const spikeQ = baseQ + intensity * 12
      masterFilter.Q.cancelScheduledValues(Tone.now())
      masterFilter.Q.setValueAtTime(spikeQ, Tone.now())
      masterFilter.Q.exponentialRampToValueAtTime(baseQ, Tone.now() + 0.3)
    }
  }

  function triggerHit() {
    if (!hitSynth || !isStarted.value) return
    const note = notes[Math.floor(Math.random() * notes.length)]
    hitSynth.triggerAttackRelease(note, '16n')
  }

  function dispose() {
    Tone.getTransport().stop()
    Tone.getTransport().cancel()
    for (const loop of loops) loop.dispose()
    loops = []
    kick?.dispose()
    hat?.dispose()
    snare?.noise.dispose()
    snare?.membrane.dispose()
    pad?.dispose()
    bass?.dispose()
    hitSynth?.dispose()
    masterFilter?.dispose()
    masterGain?.dispose()
    panner?.dispose()
  }

  return {
    isMuted,
    isStarted,
    config,
    start,
    stop,
    toggle,
    setVolume,
    setPan,
    spikeResonance,
    triggerHit,
    dispose,
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npx vitest run src/__tests__/composables/useSignalSynth.test.ts`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/composables/useSignalSynth.ts src/__tests__/composables/useSignalSynth.test.ts
git commit -m "Add useSignalSynth composable with data-driven rhythmic patterns"
```

---

### Task 5: Wire ConnectorResultView

**Files:**
- Modify: `src/views/ConnectorResultView.vue`

This task integrates both composables into the view and adds the mute toggle, volume slider, mouse-audio coupling, and scroll-volume fade.

- [ ] **Step 1: Replace physics init with `useDataDrivenPhysics`**

In `src/views/ConnectorResultView.vue`, replace the imports at line 212:

```typescript
import { useCosmicPhysics, type OrbDef } from '@/composables/useCosmicPhysics'
```

With:

```typescript
import { useDataDrivenPhysics } from '@/composables/useDataDrivenPhysics'
import { useSignalSynth, type AudioMetrics } from '@/composables/useSignalSynth'
```

- [ ] **Step 2: Remove `hexToOrbDefs` function**

Delete the entire `hexToOrbDefs` function (lines 240-250) and the `cosmicHandle` variable (line 252). Replace with:

```typescript
import { shallowRef } from 'vue'
// ... add shallowRef to the existing vue import

const cosmicHandle = shallowRef<ReturnType<typeof useDataDrivenPhysics> | null>(null)
const synthHandle = shallowRef<ReturnType<typeof useSignalSynth> | null>(null)
```

- [ ] **Step 3: Add synth refs**

After the `rawExpanded` ref (line 275), add:

```typescript
// ── Audio controls ──────────────────────────────────────────────────────
const audioVolume = ref(0.7)
```

- [ ] **Step 4: Update onMounted to use data-driven physics and synth**

Replace the physics init block in `onMounted` (lines 472-484) with:

```typescript
  // Init physics canvas — will be re-initialized with data after profile loads
  if (canvasRef.value && cfg.value) {
    cosmicHandle.value = useDataDrivenPhysics(
      canvasRef,
      null, // no profile yet
      cfg.value.physics,
      cfg.value.color,
    )
    await cosmicHandle.value.init()
  }

  // Fetch all data
  await fetchProfile()

  // Re-init physics with actual profile data
  if (profile.value && canvasRef.value && cfg.value) {
    cosmicHandle.value?.destroy()
    cosmicHandle.value = useDataDrivenPhysics(
      canvasRef,
      profile.value,
      cfg.value.physics,
      cfg.value.color,
    )
    await cosmicHandle.value.init()
  }

  // Init audio synth from profile
  if (profile.value) {
    const audio = profile.value.audio_avg as Record<string, number> | undefined
    if (audio) {
      const metrics: AudioMetrics = {
        tempo: audio.tempo ?? 120,
        energy: audio.energy ?? 0.5,
        valence: audio.valence ?? 0.5,
        danceability: audio.danceability ?? 0.5,
        acousticness: audio.acousticness ?? 0.5,
      }
      synthHandle.value = useSignalSynth(metrics)
    }
  }
```

- [ ] **Step 5: Add mouse-audio coupling**

After the `onScroll` function (line 415), add:

```typescript
// ── Mouse → audio coupling ──────────────────────────────────────────────
let lastMouseX = 0
let lastMouseY = 0
let lastMouseTime = 0

function onMouseMoveAudio(e: MouseEvent) {
  if (!synthHandle.value || synthHandle.value.isMuted.value) return

  const now = performance.now()
  const W = window.innerWidth

  // Pan based on X position
  const pan = (e.clientX / W) * 2 - 1
  synthHandle.value.setPan(pan * 0.6) // subtle, not full pan

  // Velocity → resonance spike
  if (lastMouseTime > 0) {
    const dt = Math.max(1, now - lastMouseTime)
    const dx = e.clientX - lastMouseX
    const dy = e.clientY - lastMouseY
    const velocity = Math.sqrt(dx * dx + dy * dy) / dt
    if (velocity > 1.5) {
      synthHandle.value.spikeResonance(Math.min(1, velocity / 5))
    }
  }

  lastMouseX = e.clientX
  lastMouseY = e.clientY
  lastMouseTime = now
}

function onCanvasClick(e: MouseEvent) {
  // Trigger one-shot hit
  synthHandle.value?.triggerHit()
  // Spawn particle burst via physics
  if (canvasRef.value) {
    const rect = canvasRef.value.getBoundingClientRect()
    cosmicHandle.value?.clickImpulse(e.clientX - rect.left, e.clientY - rect.top)
  }
}
```

- [ ] **Step 6: Update scroll handler for volume fade**

Replace the `onScroll` function:

```typescript
function onScroll() {
  if (!heroRef.value) return
  const rect = heroRef.value.getBoundingClientRect()
  const scrolled = -rect.top / rect.height
  canvasOpacity.value = Math.max(0.15, 1 - scrolled * 1.2)

  // Fade audio volume with scroll
  if (synthHandle.value && !synthHandle.value.isMuted.value) {
    const volumeFade = Math.max(0.05, 1 - scrolled * 0.8)
    synthHandle.value.setVolume(audioVolume.value * volumeFade)
  }
}
```

- [ ] **Step 7: Wire event listeners in onMounted/onUnmounted**

In `onMounted`, after the synth init, add:

```typescript
  window.addEventListener('mousemove', onMouseMoveAudio)
```

In `onUnmounted`, add before the existing cleanup:

```typescript
  synthHandle.value?.dispose()
  window.removeEventListener('mousemove', onMouseMoveAudio)
```

- [ ] **Step 8: Add click handler to canvas**

Add `@click="onCanvasClick"` to the canvas element in the template (line 9-13):

```html
      <canvas
        ref="canvasRef"
        class="absolute inset-0 w-full h-full transition-opacity duration-700 cursor-crosshair"
        :style="{ opacity: canvasOpacity }"
        @click="onCanvasClick"
      />
```

- [ ] **Step 9: Add mute toggle and volume slider to template**

After the "Back to calibrate" link (before the closing `</div>` of the root element, around line 200), add:

```html
    <!-- Audio controls -->
    <div v-if="synthHandle" class="fixed bottom-6 right-6 z-20 flex items-center gap-3">
      <input
        type="range"
        min="0"
        max="1"
        step="0.05"
        :value="audioVolume"
        @input="(e) => { audioVolume = Number((e.target as HTMLInputElement).value); synthHandle?.setVolume(audioVolume) }"
        class="w-20 h-1 appearance-none bg-gray-700 rounded-full cursor-pointer accent-gray-500 opacity-60 hover:opacity-100 transition-opacity"
      />
      <button
        @click="synthHandle?.toggle()"
        class="w-9 h-9 flex items-center justify-center rounded-full border border-gray-700 bg-gray-900/80 text-gray-400 hover:text-gray-200 hover:border-gray-500 transition-colors text-xs font-mono"
        :title="synthHandle?.isMuted ? 'Unmute' : 'Mute'"
      >
        {{ synthHandle?.isMuted ? '&#9835;' : '&#9834;' }}
      </button>
    </div>
```

- [ ] **Step 10: Verify build**

Run: `npm run type-check`
Expected: No errors

- [ ] **Step 11: Commit**

```bash
git add src/views/ConnectorResultView.vue
git commit -m "Wire data-driven physics + Tone.js synth into ConnectorResultView"
```

---

### Task 6: Manual Verification

- [ ] **Step 1: Start dev server**

Run: `npm run dev`

- [ ] **Step 2: Navigate to `/calibrate/spotify`**

Verify:
- Hero canvas renders with valence-driven colors (not just provider hex)
- Particle density reflects energy level
- Scroll fades canvas opacity

- [ ] **Step 3: Click the mute toggle**

Verify:
- Tone.js audio starts playing on first click
- Beat tempo matches your Spotify tempo
- Pattern density reflects your energy level
- Filter warmth reflects acousticness

- [ ] **Step 4: Test mouse interactivity**

Verify:
- Moving mouse across canvas shifts audio pan
- Fast mouse movement creates filter resonance sweep
- Clicking canvas triggers percussive hit + particle burst

- [ ] **Step 5: Test scroll-volume fade**

Verify:
- Scrolling down into The Read section fades audio volume
- Scrolling back up restores volume

- [ ] **Step 6: Check Top Genres section**

Verify:
- Genre pills render in Signal Data section (may require re-syncing Spotify)

- [ ] **Step 7: Check The Read and Cross Correlations**

Verify:
- If LLM not configured: shows "Narrative engine offline" message
- If LLM configured: narrative loads and cross-correlations render

- [ ] **Step 8: Run full test suite**

Run: `npm run test`
Expected: All tests pass

- [ ] **Step 9: Run build check**

Run: `npm run build`
Expected: Build succeeds with no TypeScript errors

- [ ] **Step 10: Final commit if any fixes needed**

```bash
git add -A
git commit -m "Polish sonic canvas after manual testing"
```
