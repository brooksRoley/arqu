# Glass Studio — Subliminal / Entrainment Authoring (Design Spec)

Date: 2026-08-04
Route: `/studio` (`src/views/GlassView.vue`)

## Goal
Turn `/studio` from a single fixed-text overlay tool into an authoring studio for
subliminal-message + binaural-entrainment media. The user uploads a video/audio,
layers customizable text (fonts, position, timing, effects), runs real binaural-beat
entrainment, and **exports a file with everything baked in**.

## Mission fit
Runs entirely on already-installed packages (Canvas + Web Audio + Tone.js). No paid
APIs, no embeddings. Self-expression + hypnosis/entrainment + ritual pillars.

## Core architectural decision (non-negotiable)
**One shared canvas renderer for both live preview and export.** Today preview is a DOM
`<h1>` and export re-draws text on a canvas — two code paths that drift. Collapse them:
a `useGlassComposer` exposes `drawFrame(ctx, t, layers, size)` that renders one frame from
the composition at clock time `t`. Live preview calls it every `requestAnimationFrame`
over the video; `useGlassExport` calls the **same** function into the export canvas. This
guarantees subliminal flashes and motion are frame-accurate in the downloaded file.

## Data model
```ts
// src/composables/studioTypes.ts (Foundation owns)
type Anchor = 'tl'|'tc'|'tr'|'cl'|'cc'|'cr'|'bl'|'bc'|'br'  // 9-grid
type BlendMode = 'normal'|'exclusion'|'difference'|'screen'|'overlay'|'multiply'
type TimingMode = 'persistent'|'sequence'|'subliminal'
type MotionType = 'none'|'pulse'|'drift'|'zoom'|'shake'|'waver'

interface TextLayer {
  id: string
  content: string[]                 // 1 = static; many = sequence/flash pool
  font:  { family: string; sizeVw: number; weight: number; letterSpacing: number; upper: boolean }
  pos:   { anchor: Anchor; dx: number; dy: number }   // dx/dy in % of viewport
  style: { color: string; opacity: number; blend: BlendMode }
  timing:{ mode: TimingMode; holdMs: number; fadeMs: number; intervalMs: number; flashMs: number }
  motion:{ type: MotionType; amount: number; syncToBeat: boolean }
}

interface BinauralConfig {
  enabled: boolean
  mode: 'preset'|'journey'
  band: Band                        // 'delta'|'theta'|'alpha'|'beta'|'gamma'  (preset mode)
  journey: { band: Band; durationS: number }[]  // journey mode, auto-fit to media length
  volume: number                    // 0..100
}

interface GlassComposition {
  textLayers: TextLayer[]
  binaural: BinauralConfig
  recipeId?: string
}
```
Text is a **list of layers** so a persistent title and a flashing-affirmation pool can run
at once. **Motion is additive** — it composes on top of any timing mode.

## Text overlay engine (all four behaviors)
Per layer, `drawFrame` computes an effective `{ text, alpha, transform }` for time `t`:
- **persistent** — `content[0]`, alpha = opacity (fade in once at start via `fadeMs`).
- **sequence** — cycle `content[]`: each shows `holdMs` with `fadeMs` in/out, then next.
  Loops. Full cycle = `content.length * (holdMs + 2*fadeMs)`.
- **subliminal** — every `intervalMs`, flash one `content[]` item for `flashMs` (hard on/off,
  pool advances each flash; randomize order). Export is 30fps → document `flashMs >= ~33ms`
  as the practical floor (true single-frame ≈ 33ms).
- **motion (additive)** — apply a per-frame transform: `pulse`/`waver` scale/opacity osc,
  `drift` slow translate, `zoom` slow scale, `shake` jitter. `syncToBeat:true` drives the
  oscillator from the active binaural beat Hz (else a default rate).
Rendering: `ctx.font` from layer font; anchor→x/y from 9-grid + dx/dy; `globalCompositeOperation`
= blend; `globalAlpha` = computed alpha; word-wrap to viewport width; `upper` → uppercase.

## Binaural entrainment (curated: presets + journey, no raw sliders)
`src/composables/useStudioBinaural.ts` wraps the existing `useBinauralEngine`
(`setBeat(beatHz, carrierHz, ramp)`, `setVolume`, `getWaveformData`, `destroy`).
- **Band presets** — Delta/Theta/Alpha/Beta/Gamma buttons. Each maps to a
  `{ beatHz, carrierHz }` (see BANDS below) and shows a short explanation card + a
  deep-dive link to the matching `/learn` article.
- **Journey mode** — an ordered list of bands with durations, auto-fit to media length; a
  scheduler advances phases on the composer clock and calls `setBeat` with a ramp at each
  transition (mirrors `useAdaptiveEntrain`'s arc, simplified).
- **Export capture** — binaural output node must be routed into the export
  `MediaStreamAudioDestinationNode` alongside media audio + Tone master, so the beat is in
  the file. (Foundation exposes the export audio-dest seam; Binaural agent connects to it.)
BANDS (beat Hz @ carrier Hz): delta 2@180, theta 6@200, alpha 10@210, beta 18@220, gamma 40@220.
Reuse honest framing from `src/data/learn.ts` — do not overclaim.

## Teaching: recipes + deep-dive links (no inline prose, no first-run tour)
`src/data/glassRecipes.ts` — array of named `GlassComposition` presets that teach by example,
e.g. "Confidence subliminal" (Theta journey + 200ms flashed affirmations, centered, low opacity),
"Calm descent" (Alpha→Theta journey + persistent breath cue), "Focus field" (Gamma preset +
sequence cues). A recipe bar applies a recipe into the live composition (user edits from there).
Deep-dive links point to existing `/learn` slugs on binaural beats / isochronic tones / bands.

## UI (in GlassView, bottom control area → tabbed panels)
Keep the viewport + transport. Replace the single crowded tool row with compact tabs:
**Text** (layer list; per-layer font/size/weight/case, 9-grid position, color/opacity/blend,
timing mode + its params, motion) · **Sound** (binaural enable, preset vs journey, band cards
w/ links, volume; existing glass tone presets remain here too) · **Recipes** (recipe chips +
learn links). Mobile-friendly (existing pattern uses flex-wrap + small controls).

## Export changes (`useGlassExport.ts`)
- Draw overlays via `useGlassComposer.drawFrame` (drop the bespoke text draw).
- Audio: merge media audio + Tone master (existing) + binaural node (new) into the dest.
- Keep real-time capture, mime pick, progress, cancel.

## Non-goals (YAGNI)
Full keyframe timeline; raw carrier/beat sliders; per-word karaoke; saving comps to backend
(local/in-memory only for now); isochronic tones (binaural only this pass).

## Testing / verification
No backend. Verify: `npm run build` (vue-tsc + vite) clean. Manual: each timing mode renders
in preview AND survives export (spot-check a short clip); binaural audible + in exported file;
recipe apply populates controls; learn links resolve. Add lightweight unit tests for pure
timing math (sequence/subliminal `{text,alpha}` at given `t`) and journey phase-at-time if a
JS test runner is present; otherwise keep timing logic in pure functions for testability.

## Build order (subagents, sequential — shared files)
1. **Foundation + text engine** — studioTypes, useGlassComposer (all 4 text modes), refactor
   GlassView preview to composer, refactor useGlassExport to reuse it + expose audio-dest seam,
   Text controls panel. Ships persistent+sequence+subliminal+motion end-to-end incl. export.
2. **Binaural** — useStudioBinaural (presets + journey), Sound panel band cards + links, wire
   binaural node into the export audio dest seam from step 1.
3. **Recipes + teaching** — glassRecipes data, Recipes panel (apply + deep-dive links).
