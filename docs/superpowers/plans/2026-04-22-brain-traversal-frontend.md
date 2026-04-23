# Brain Traversal — Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `/brain` — a full-screen spatial image library where users navigate a UMAP-projected map, traverse similarity paths into a sequence, compose geometry/audio/narration automatically from vibe curves, and export to MP4.

**Architecture:** Two canvas modes (MapCanvas top-down / LocalCanvas neighbor orbit) controlled by `BrainView.vue`. Five composables handle map rendering, local view, sequence state, composition, and export. Composition parameters are derived automatically from the vibe curve returned by the backend — no manual configuration required by default. Extends the existing `useGlassExport` pattern for MP4 output.

**Tech Stack:** Vue 3, TypeScript, Canvas 2D API, Tone.js (CDN, already present), `useAuthStore.apiFetch`, Tailwind

**Prerequisite:** Backend plan `2026-04-22-brain-traversal-backend.md` must be deployed before this plan executes.

---

## File Map

| Action | File |
|---|---|
| Modify | `src/router/index.ts` — add `/brain` route |
| Create | `src/composables/useBrainMap.ts` |
| Create | `src/composables/useBrainLocal.ts` |
| Create | `src/composables/useBrainSequence.ts` |
| Create | `src/composables/useBrainComposer.ts` |
| Create | `src/composables/useBrainExport.ts` |
| Create | `src/views/BrainView.vue` |

---

## Task 1: Add /brain route

**Files:**
- Modify: `src/router/index.ts`

- [ ] **Step 1: Add the route**

In `src/router/index.ts`, find the authenticated routes block and add:

```typescript
{
  path: '/brain',
  name: 'brain',
  component: () => import('@/views/BrainView.vue'),
  meta: { requiresAuth: true }
},
```

- [ ] **Step 2: Build check**

```bash
npm run build -- --noEmit 2>&1 | tail -5
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add src/router/index.ts
git commit -m "Add /brain route"
```

---

## Task 2: useBrainMap — top-down UMAP canvas

**Files:**
- Create: `src/composables/useBrainMap.ts`

- [ ] **Step 1: Create the composable**

```typescript
// src/composables/useBrainMap.ts
import { ref, onUnmounted } from 'vue'
import type { Ref } from 'vue'
import { useAuthStore } from './useAuthStore'

export interface MapImage {
  id: string
  blob_url: string
  filename: string | null
  vibe_dimensions: { energy: number; warmth: number; density: number; intimacy: number; motion: number } | null
  map_x: number | null
  map_y: number | null
}

interface PanState {
  panX: number
  panY: number
  zoom: number
  dragging: boolean
  dragStart: { x: number; y: number; panX: number; panY: number } | null
}

const CANVAS_UNITS = 1000
const THUMB_SIZE = 72
const MIN_ZOOM = 0.3
const MAX_ZOOM = 4.0

export function useBrainMap(canvasRef: Ref<HTMLCanvasElement | null>) {
  const auth = useAuthStore()
  const images = ref<MapImage[]>([])
  const loading = ref(false)
  const visitedIds = ref<Set<string>>(new Set())

  const state: PanState = { panX: 0, panY: 0, zoom: 1, dragging: false, dragStart: null }
  const thumbCache = new Map<string, HTMLImageElement>()
  let rafId = 0

  async function loadMap() {
    loading.value = true
    try {
      const data = await auth.apiFetch('/api/brain/map')
      images.value = data
    } finally {
      loading.value = false
    }
  }

  function worldToScreen(wx: number, wy: number, canvas: HTMLCanvasElement) {
    return {
      x: canvas.width / 2 + (wx - CANVAS_UNITS / 2) * state.zoom + state.panX,
      y: canvas.height / 2 + (wy - CANVAS_UNITS / 2) * state.zoom + state.panY,
    }
  }

  function screenToWorld(sx: number, sy: number, canvas: HTMLCanvasElement) {
    return {
      x: (sx - canvas.width / 2 - state.panX) / state.zoom + CANVAS_UNITS / 2,
      y: (sy - canvas.height / 2 - state.panY) / state.zoom + CANVAS_UNITS / 2,
    }
  }

  function getThumb(img: MapImage): HTMLImageElement | null {
    if (thumbCache.has(img.id)) return thumbCache.get(img.id)!
    const el = new Image()
    el.src = img.blob_url
    el.onload = () => thumbCache.set(img.id, el)
    return null
  }

  function vibeDot(vd: MapImage['vibe_dimensions']): string {
    if (!vd) return '#6366f1'
    const h = Math.round(vd.warmth * 60)  // 0=cool blue, 60=warm amber
    const l = Math.round(30 + vd.energy * 40)
    return `hsl(${h}, 80%, ${l}%)`
  }

  function draw() {
    const canvas = canvasRef.value
    if (!canvas) return
    const ctx = canvas.getContext('2d')!
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    // Background
    ctx.fillStyle = '#0a0a0f'
    ctx.fillRect(0, 0, canvas.width, canvas.height)

    // Vignette
    const vg = ctx.createRadialGradient(
      canvas.width / 2, canvas.height / 2, canvas.width * 0.3,
      canvas.width / 2, canvas.height / 2, canvas.width * 0.75,
    )
    vg.addColorStop(0, 'rgba(0,0,0,0)')
    vg.addColorStop(1, 'rgba(0,0,0,0.7)')
    ctx.fillStyle = vg
    ctx.fillRect(0, 0, canvas.width, canvas.height)

    const imgs = images.value
    const showThumbs = state.zoom >= 0.7

    for (const img of imgs) {
      const wx = img.map_x ?? 500
      const wy = img.map_y ?? 500
      const { x, y } = worldToScreen(wx, wy, canvas)
      const sz = THUMB_SIZE * state.zoom

      if (x < -sz || x > canvas.width + sz || y < -sz || y > canvas.height + sz) continue

      const isVisited = visitedIds.value.has(img.id)
      const dotColor = vibeDot(img.vibe_dimensions)

      if (showThumbs) {
        const thumb = getThumb(img)
        if (thumb) {
          ctx.save()
          ctx.globalAlpha = isVisited ? 0.45 : 0.92
          // Glow
          const energy = img.vibe_dimensions?.energy ?? 0.5
          ctx.shadowColor = dotColor
          ctx.shadowBlur = 8 + energy * 14
          // Clip to rounded rect
          const rx = x - sz / 2, ry = y - sz / 2
          ctx.beginPath()
          ctx.roundRect(rx, ry, sz, sz, sz * 0.12)
          ctx.clip()
          ctx.drawImage(thumb, rx, ry, sz, sz)
          ctx.restore()
        } else {
          // Fallback dot while loading
          ctx.beginPath()
          ctx.arc(x, y, sz * 0.25, 0, Math.PI * 2)
          ctx.fillStyle = dotColor
          ctx.fill()
        }
      } else {
        // Zoomed out: color dot
        const r = Math.max(3, 5 * state.zoom)
        ctx.beginPath()
        ctx.arc(x, y, r, 0, Math.PI * 2)
        ctx.fillStyle = dotColor
        ctx.globalAlpha = isVisited ? 0.35 : 0.85
        ctx.fill()
        ctx.globalAlpha = 1
      }
    }

    rafId = requestAnimationFrame(draw)
  }

  function hitTest(sx: number, sy: number, canvas: HTMLCanvasElement): MapImage | null {
    const sz = THUMB_SIZE * state.zoom
    for (const img of images.value) {
      const wx = img.map_x ?? 500
      const wy = img.map_y ?? 500
      const { x, y } = worldToScreen(wx, wy, canvas)
      const dx = sx - x, dy = sy - y
      if (dx * dx + dy * dy < (sz / 2) * (sz / 2)) return img
    }
    return null
  }

  function onMouseDown(e: MouseEvent) {
    state.dragging = true
    state.dragStart = { x: e.clientX, y: e.clientY, panX: state.panX, panY: state.panY }
  }

  function onMouseMove(e: MouseEvent) {
    if (!state.dragging || !state.dragStart) return
    state.panX = state.dragStart.panX + (e.clientX - state.dragStart.x)
    state.panY = state.dragStart.panY + (e.clientY - state.dragStart.y)
  }

  function onMouseUp(e: MouseEvent) {
    const wasDrag = state.dragging && state.dragStart &&
      (Math.abs(e.clientX - state.dragStart.x) > 4 || Math.abs(e.clientY - state.dragStart.y) > 4)
    state.dragging = false
    state.dragStart = null
    return !wasDrag  // true = was a tap, not a drag
  }

  function onWheel(e: WheelEvent) {
    e.preventDefault()
    const delta = e.deltaY > 0 ? 0.9 : 1.1
    state.zoom = Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, state.zoom * delta))
  }

  function start() {
    rafId = requestAnimationFrame(draw)
  }

  function stop() {
    cancelAnimationFrame(rafId)
  }

  function markVisited(id: string) {
    visitedIds.value.add(id)
  }

  onUnmounted(stop)

  return {
    images,
    loading,
    visitedIds,
    loadMap,
    start,
    stop,
    hitTest,
    markVisited,
    onMouseDown,
    onMouseMove,
    onMouseUp,
    onWheel,
  }
}
```

- [ ] **Step 2: Build check**

```bash
npm run build -- --noEmit 2>&1 | tail -5
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add src/composables/useBrainMap.ts
git commit -m "Add useBrainMap top-down UMAP canvas composable"
```

---

## Task 3: useBrainLocal — neighbor orbit view

**Files:**
- Create: `src/composables/useBrainLocal.ts`

- [ ] **Step 1: Create the composable**

```typescript
// src/composables/useBrainLocal.ts
import { ref, onUnmounted } from 'vue'
import type { Ref } from 'vue'
import { useAuthStore } from './useAuthStore'
import type { MapImage } from './useBrainMap'

export interface Neighbor {
  image: MapImage
  similarity: number
  angle: number   // radians, computed client-side
  radius: number  // px
}

const FOCAL_SIZE = 220
const MIN_RADIUS = 100
const MAX_RADIUS = 260

export function useBrainLocal(canvasRef: Ref<HTMLCanvasElement | null>) {
  const auth = useAuthStore()
  const focal = ref<MapImage | null>(null)
  const neighbors = ref<Neighbor[]>([])
  const loadingNeighbors = ref(false)
  const visitedIds = ref<Set<string>>(new Set())
  const thumbCache = new Map<string, HTMLImageElement>()
  let rafId = 0

  async function setFocal(img: MapImage) {
    focal.value = img
    visitedIds.value.add(img.id)
    await loadNeighbors(img.id)
  }

  async function loadNeighbors(imageId: string) {
    loadingNeighbors.value = true
    try {
      const exclude = [...visitedIds.value].join(',')
      const data = await auth.apiFetch(
        `/api/brain/traverse?image_id=${imageId}&exclude=${exclude}`
      )
      const branches: Array<{ id: string; blob_url: string; filename: string; similarity: number }> =
        data.branches ?? []

      // Arrange neighbors in orbit — evenly spaced angles, radius from similarity
      neighbors.value = branches.map((b, i) => {
        const angle = (i / branches.length) * Math.PI * 2 - Math.PI / 2
        const radius = MIN_RADIUS + (1 - b.similarity) * (MAX_RADIUS - MIN_RADIUS)
        return {
          image: {
            id: b.id,
            blob_url: b.blob_url,
            filename: b.filename,
            vibe_dimensions: null,
            map_x: null,
            map_y: null,
          },
          similarity: b.similarity,
          angle,
          radius,
        }
      })
    } finally {
      loadingNeighbors.value = false
    }
  }

  function getThumb(blobUrl: string, id: string): HTMLImageElement | null {
    if (thumbCache.has(id)) return thumbCache.get(id)!
    const el = new Image()
    el.src = blobUrl
    el.onload = () => thumbCache.set(id, el)
    return null
  }

  function draw() {
    const canvas = canvasRef.value
    if (!canvas) return
    const ctx = canvas.getContext('2d')!
    const cx = canvas.width / 2
    const cy = canvas.height / 2

    ctx.clearRect(0, 0, canvas.width, canvas.height)
    ctx.fillStyle = '#0a0a0f'
    ctx.fillRect(0, 0, canvas.width, canvas.height)

    // Draw orbit lines
    ctx.strokeStyle = 'rgba(99,102,241,0.12)'
    ctx.lineWidth = 1
    for (const n of neighbors.value) {
      const nx = cx + Math.cos(n.angle) * n.radius
      const ny = cy + Math.sin(n.angle) * n.radius
      ctx.beginPath()
      ctx.moveTo(cx, cy)
      ctx.lineTo(nx, ny)
      ctx.stroke()
    }

    // Draw neighbors
    for (const n of neighbors.value) {
      const nx = cx + Math.cos(n.angle) * n.radius
      const ny = cy + Math.sin(n.angle) * n.radius
      const sz = 72 + n.similarity * 32
      const thumb = getThumb(n.image.blob_url, n.image.id)
      const isVisited = visitedIds.value.has(n.image.id)

      ctx.save()
      ctx.globalAlpha = isVisited ? 0.3 : 0.88
      if (thumb) {
        ctx.shadowColor = `rgba(139,92,246,${n.similarity})`
        ctx.shadowBlur = 12
        ctx.beginPath()
        ctx.roundRect(nx - sz / 2, ny - sz / 2, sz, sz, sz * 0.12)
        ctx.clip()
        ctx.drawImage(thumb, nx - sz / 2, ny - sz / 2, sz, sz)
      } else {
        ctx.beginPath()
        ctx.arc(nx, ny, sz / 2, 0, Math.PI * 2)
        ctx.fillStyle = '#6366f1'
        ctx.fill()
      }
      ctx.restore()

      // Similarity badge
      ctx.fillStyle = 'rgba(255,255,255,0.55)'
      ctx.font = '10px Inter, sans-serif'
      ctx.textAlign = 'center'
      ctx.fillText(`${Math.round(n.similarity * 100)}%`, nx, ny + sz / 2 + 14)
    }

    // Draw focal image
    const foc = focal.value
    if (foc) {
      const thumb = getThumb(foc.blob_url, foc.id)
      ctx.save()
      ctx.shadowColor = 'rgba(139,92,246,0.6)'
      ctx.shadowBlur = 30
      if (thumb) {
        ctx.beginPath()
        ctx.roundRect(cx - FOCAL_SIZE / 2, cy - FOCAL_SIZE / 2, FOCAL_SIZE, FOCAL_SIZE, FOCAL_SIZE * 0.1)
        ctx.clip()
        ctx.drawImage(thumb, cx - FOCAL_SIZE / 2, cy - FOCAL_SIZE / 2, FOCAL_SIZE, FOCAL_SIZE)
      } else {
        ctx.beginPath()
        ctx.arc(cx, cy, FOCAL_SIZE / 2, 0, Math.PI * 2)
        ctx.fillStyle = '#4f46e5'
        ctx.fill()
      }
      ctx.restore()
    }

    // Vignette
    const vg = ctx.createRadialGradient(cx, cy, canvas.width * 0.25, cx, cy, canvas.width * 0.65)
    vg.addColorStop(0, 'rgba(0,0,0,0)')
    vg.addColorStop(1, 'rgba(0,0,0,0.65)')
    ctx.fillStyle = vg
    ctx.fillRect(0, 0, canvas.width, canvas.height)

    rafId = requestAnimationFrame(draw)
  }

  function hitTestNeighbor(sx: number, sy: number): Neighbor | null {
    const canvas = canvasRef.value
    if (!canvas) return null
    const cx = canvas.width / 2
    const cy = canvas.height / 2
    for (const n of neighbors.value) {
      const nx = cx + Math.cos(n.angle) * n.radius
      const ny = cy + Math.sin(n.angle) * n.radius
      const sz = 72 + n.similarity * 32
      const dx = sx - nx, dy = sy - ny
      if (dx * dx + dy * dy < (sz / 2) * (sz / 2)) return n
    }
    return null
  }

  function start() { rafId = requestAnimationFrame(draw) }
  function stop() { cancelAnimationFrame(rafId) }
  onUnmounted(stop)

  return { focal, neighbors, loadingNeighbors, visitedIds, setFocal, hitTestNeighbor, start, stop }
}
```

- [ ] **Step 2: Build check**

```bash
npm run build -- --noEmit 2>&1 | tail -5
```

- [ ] **Step 3: Commit**

```bash
git add src/composables/useBrainLocal.ts
git commit -m "Add useBrainLocal neighbor orbit composable"
```

---

## Task 4: useBrainSequence — sequence strip + vibe curve + compose API

**Files:**
- Create: `src/composables/useBrainSequence.ts`

- [ ] **Step 1: Create the composable**

```typescript
// src/composables/useBrainSequence.ts
import { ref, computed } from 'vue'
import { useAuthStore } from './useAuthStore'
import type { MapImage } from './useBrainMap'

export interface TransitionDescriptor {
  from_id: string
  to_id: string
  similarity: number
  color_shift: string
  mood_shift: number
  subject_continuity: boolean
  transition_type: 'dissolve' | 'flash_cut' | 'slow_zoom' | 'hard_cut'
  duration: number
}

export interface ComposeResult {
  transitions: TransitionDescriptor[]
  vibe_curve: Record<string, number[]>
}

const DIM_COLORS: Record<string, string> = {
  energy: '#f59e0b',
  warmth: '#ef4444',
  density: '#8b5cf6',
  intimacy: '#ec4899',
  motion: '#06b6d4',
}

export function useBrainSequence() {
  const auth = useAuthStore()
  const items = ref<MapImage[]>([])
  const compose = ref<ComposeResult | null>(null)
  const composing = ref(false)

  const canCompose = computed(() => items.value.length >= 2)

  function addImage(img: MapImage) {
    if (!items.value.find(i => i.id === img.id)) {
      items.value.push(img)
    }
    if (canCompose.value) triggerCompose()
  }

  function removeAt(idx: number) {
    items.value.splice(idx, 1)
    compose.value = null
    if (canCompose.value) triggerCompose()
  }

  function move(fromIdx: number, toIdx: number) {
    const item = items.value.splice(fromIdx, 1)[0]
    items.value.splice(toIdx, 0, item)
    if (canCompose.value) triggerCompose()
  }

  let composeDebounce: ReturnType<typeof setTimeout> | null = null

  function triggerCompose() {
    if (composeDebounce) clearTimeout(composeDebounce)
    composeDebounce = setTimeout(runCompose, 400)
  }

  async function runCompose() {
    if (!canCompose.value) return
    composing.value = true
    try {
      const result = await auth.apiFetch('/api/brain/sequence/compose', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image_ids: items.value.map(i => i.id) }),
      })
      compose.value = result
    } catch (e) {
      console.error('compose failed', e)
    } finally {
      composing.value = false
    }
  }

  /** Draw the vibe curve above the sequence strip onto a canvas element. */
  function drawVibeCurve(canvas: HTMLCanvasElement) {
    const curve = compose.value?.vibe_curve
    if (!curve || items.value.length < 2) return
    const ctx = canvas.getContext('2d')!
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    const dims = ['energy', 'warmth', 'density', 'intimacy', 'motion']
    const n = items.value.length

    for (const dim of dims) {
      const vals = curve[dim] ?? []
      if (!vals.length) continue
      ctx.beginPath()
      ctx.strokeStyle = DIM_COLORS[dim] ?? '#fff'
      ctx.lineWidth = 1.5
      ctx.globalAlpha = 0.7
      for (let i = 0; i < vals.length; i++) {
        const x = (i / (n - 1)) * canvas.width
        const y = canvas.height - vals[i] * canvas.height * 0.85 - canvas.height * 0.075
        if (i === 0) ctx.moveTo(x, y)
        else ctx.lineTo(x, y)
      }
      ctx.stroke()
    }
    ctx.globalAlpha = 1
  }

  return {
    items,
    compose,
    composing,
    canCompose,
    addImage,
    removeAt,
    move,
    drawVibeCurve,
    DIM_COLORS,
  }
}
```

- [ ] **Step 2: Build check**

```bash
npm run build -- --noEmit 2>&1 | tail -5
```

- [ ] **Step 3: Commit**

```bash
git add src/composables/useBrainSequence.ts
git commit -m "Add useBrainSequence strip, vibe curve, and compose API composable"
```

---

## Task 5: useBrainComposer — geometry + sound + narration

**Files:**
- Create: `src/composables/useBrainComposer.ts`

- [ ] **Step 1: Create the composable**

```typescript
// src/composables/useBrainComposer.ts
import { ref, onUnmounted } from 'vue'
import type { ComposeResult, TransitionDescriptor } from './useBrainSequence'
import type { MapImage } from './useBrainMap'
import { useAuthStore } from './useAuthStore'

declare const Tone: any  // loaded via CDN

export interface ComposerFrame {
  image: MapImage
  holdDuration: number  // seconds
  transition: TransitionDescriptor | null
}

export function useBrainComposer() {
  const auth = useAuthStore()
  const narration = ref<string[]>([])  // one caption per image
  const generatingNarration = ref(false)
  let synth: any = null
  let toneStarted = false

  function buildFrames(images: MapImage[], compose: ComposeResult | null): ComposerFrame[] {
    return images.map((img, i) => {
      const vd = img.vibe_dimensions
      const energy = vd?.energy ?? 0.5
      const holdDuration = 2.0 + (1.0 - energy) * 2.0  // low energy = longer hold
      const transition = compose?.transitions.find(t => t.from_id === img.id) ?? null
      return { image: img, holdDuration, transition }
    })
  }

  /**
   * Draw geometry overlays for a given frame onto an overlay canvas.
   * Call this once per frame during export render.
   */
  function drawGeometry(
    ctx: CanvasRenderingContext2D,
    frame: ComposerFrame,
    progress: number,  // 0-1 within hold
    width: number,
    height: number,
  ) {
    const vd = frame.image.vibe_dimensions
    const energy = vd?.energy ?? 0.5
    const warmth = vd?.warmth ?? 0.5
    const density = vd?.density ?? 0.5
    const intimacy = vd?.intimacy ?? 0.5
    const motion = vd?.motion ?? 0.5

    ctx.save()

    // Color temperature overlay tint
    const hue = Math.round(warmth * 55)  // 0=blue/cool, 55=amber/warm
    ctx.fillStyle = `hsla(${hue}, 70%, 50%, 0.04)`
    ctx.fillRect(0, 0, width, height)

    // Pulsing circle — energy driven
    const pulsePhase = Math.sin(progress * Math.PI * 2 * (1 + energy * 3))
    const circleR = Math.min(width, height) * (0.08 + energy * 0.06 + pulsePhase * 0.015)
    const cx = width / 2, cy = height / 2
    ctx.beginPath()
    ctx.arc(cx, cy, circleR, 0, Math.PI * 2)
    ctx.strokeStyle = `hsla(${hue + 20}, 80%, 70%, ${0.15 + energy * 0.2})`
    ctx.lineWidth = 1.5
    ctx.stroke()

    // Line grid — density driven
    const lineCount = Math.round(density * 5)
    ctx.strokeStyle = `hsla(270, 60%, 70%, 0.06)`
    ctx.lineWidth = 0.8
    for (let i = 1; i <= lineCount; i++) {
      const y = (i / (lineCount + 1)) * height
      ctx.beginPath()
      ctx.moveTo(0, y)
      ctx.lineTo(width, y)
      ctx.stroke()
    }

    // Subject continuity ghost — echo previous frame element
    if (frame.transition?.subject_continuity) {
      ctx.beginPath()
      ctx.arc(cx, cy, circleR * 1.4, 0, Math.PI * 2)
      ctx.strokeStyle = `hsla(${hue}, 60%, 80%, 0.06)`
      ctx.lineWidth = 1
      ctx.stroke()
    }

    // Intimacy: zoom crop effect — handled externally via canvas transform, hint here
    // (Actual zoom is applied by the export renderer using intimacy value)

    ctx.restore()
  }

  async function startAudio(compose: ComposeResult | null) {
    if (!compose || typeof Tone === 'undefined') return
    try {
      if (!toneStarted) {
        await Tone.start()
        toneStarted = true
      }
      if (synth) { synth.dispose(); synth = null }

      const energy = compose.vibe_curve['energy']?.[0] ?? 0.5
      const warmth = compose.vibe_curve['warmth']?.[0] ?? 0.5
      // Warm = major-ish (higher 3rd), cool = minor-ish
      const detune = (warmth - 0.5) * 200  // ±100 cents

      synth = new Tone.PolySynth(Tone.Synth, {
        oscillator: { type: 'sine' },
        envelope: { attack: 2, decay: 0.5, sustain: 0.8, release: 3 },
      }).toDestination()
      synth.set({ detune })

      const bpm = Math.round(60 + energy * 60)  // 60-120 BPM
      Tone.getTransport().bpm.value = bpm

      // Root drone
      const root = warmth > 0.5 ? 'C3' : 'A2'
      synth.triggerAttack(root, Tone.now(), 0.15)
    } catch (e) {
      console.warn('Tone.js audio start failed', e)
    }
  }

  function stopAudio() {
    try {
      if (synth) { synth.releaseAll(); synth.dispose(); synth = null }
      if (toneStarted) Tone.getTransport().stop()
    } catch {}
  }

  async function generateNarration(images: MapImage[], compose: ComposeResult | null) {
    if (!compose || !images.length) return
    generatingNarration.value = true
    try {
      const arc = Object.entries(compose.vibe_curve)
        .map(([k, v]) => `${k}: [${v.map(n => n.toFixed(2)).join(', ')}]`)
        .join('\n')
      const descriptions = images.map((img, i) => `${i + 1}. ${img.vibe_dimensions ? JSON.stringify(img.vibe_dimensions) : 'no data'}`).join('\n')
      const result = await auth.apiFetch('/api/llm/narrate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: `You are a poetic narrator for a visual sequence. Given this emotional arc:\n${arc}\n\nWrite a short evocative caption (under 12 words) for each of ${images.length} images. Return a JSON array of strings.`,
        }),
      })
      narration.value = Array.isArray(result?.captions) ? result.captions : []
    } catch (e) {
      console.warn('Narration generation failed', e)
      narration.value = images.map(() => '')
    } finally {
      generatingNarration.value = false
    }
  }

  onUnmounted(stopAudio)

  return {
    narration,
    generatingNarration,
    buildFrames,
    drawGeometry,
    startAudio,
    stopAudio,
    generateNarration,
  }
}
```

- [ ] **Step 2: Build check**

```bash
npm run build -- --noEmit 2>&1 | tail -5
```

- [ ] **Step 3: Commit**

```bash
git add src/composables/useBrainComposer.ts
git commit -m "Add useBrainComposer geometry, audio, and narration composable"
```

---

## Task 6: useBrainExport — MP4 export pipeline

**Files:**
- Create: `src/composables/useBrainExport.ts`

- [ ] **Step 1: Create the composable**

```typescript
// src/composables/useBrainExport.ts
import { ref } from 'vue'
import type { ComposerFrame } from './useBrainComposer'

declare const Tone: any

export function useBrainExport() {
  const exporting = ref(false)
  const exportProgress = ref(0)  // 0-1

  function pickMimeType(): string {
    const candidates = ['video/mp4', 'video/webm;codecs=vp9', 'video/webm']
    for (const c of candidates) {
      if (MediaRecorder.isTypeSupported(c)) return c
    }
    return 'video/webm'
  }

  async function exportMp4(
    frames: ComposerFrame[],
    narration: string[],
    drawGeometry: (ctx: CanvasRenderingContext2D, frame: ComposerFrame, progress: number, w: number, h: number) => void,
    width = 1080,
    height = 1080,
    fps = 30,
  ): Promise<void> {
    exporting.value = true
    exportProgress.value = 0

    const canvas = document.createElement('canvas')
    canvas.width = width
    canvas.height = height
    const ctx = canvas.getContext('2d')!

    const mimeType = pickMimeType()
    const stream = canvas.captureStream(fps)

    // Merge Tone.js audio if available
    if (typeof Tone !== 'undefined') {
      try {
        const audioCtx = Tone.getContext().rawContext as AudioContext
        const dest = audioCtx.createMediaStreamDestination()
        Tone.getDestination().connect(dest)
        dest.stream.getAudioTracks().forEach(t => stream.addTrack(t))
      } catch {}
    }

    const chunks: Blob[] = []
    const recorder = new MediaRecorder(stream, { mimeType })
    recorder.ondataavailable = e => { if (e.data.size > 0) chunks.push(e.data) }

    const done = new Promise<void>(resolve => {
      recorder.onstop = () => resolve()
    })

    recorder.start()

    const thumbs = await preloadImages(frames)
    const totalDuration = frames.reduce((s, f) => s + f.holdDuration + (f.transition?.duration ?? 0), 0)
    let elapsed = 0

    for (let fi = 0; fi < frames.length; fi++) {
      const frame = frames[fi]
      const thumb = thumbs[fi]

      // Hold phase
      const holdFrames = Math.round(frame.holdDuration * fps)
      for (let f = 0; f < holdFrames; f++) {
        const progress = f / holdFrames
        ctx.clearRect(0, 0, width, height)
        if (thumb) ctx.drawImage(thumb, 0, 0, width, height)
        drawGeometry(ctx, frame, progress, width, height)
        drawNarrationText(ctx, narration[fi] ?? '', width, height)
        exportProgress.value = (elapsed + f / fps) / totalDuration
        await nextFrame()
      }
      elapsed += frame.holdDuration

      // Transition phase
      if (frame.transition && fi < frames.length - 1) {
        const nextThumb = thumbs[fi + 1]
        const transFrames = Math.round(frame.transition.duration * fps)
        for (let f = 0; f < transFrames; f++) {
          const t = f / transFrames
          ctx.clearRect(0, 0, width, height)
          applyTransition(ctx, thumb, nextThumb, frame.transition.transition_type, t, width, height)
          exportProgress.value = (elapsed + f / fps) / totalDuration
          await nextFrame()
        }
        elapsed += frame.transition.duration
      }
    }

    recorder.stop()
    await done

    const blob = new Blob(chunks, { type: mimeType })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `brain-sequence-${Date.now()}.${mimeType.includes('mp4') ? 'mp4' : 'webm'}`
    a.click()
    URL.revokeObjectURL(url)

    exporting.value = false
    exportProgress.value = 0
  }

  function applyTransition(
    ctx: CanvasRenderingContext2D,
    from: HTMLImageElement | null,
    to: HTMLImageElement | null,
    type: string,
    t: number,
    w: number,
    h: number,
  ) {
    if (type === 'dissolve') {
      if (from) { ctx.globalAlpha = 1 - t; ctx.drawImage(from, 0, 0, w, h) }
      if (to) { ctx.globalAlpha = t; ctx.drawImage(to, 0, 0, w, h) }
      ctx.globalAlpha = 1
    } else if (type === 'flash_cut') {
      const flash = t < 0.15 ? (1 - t / 0.15) : t < 0.85 ? 0 : (t - 0.85) / 0.15
      if (t < 0.5 && from) ctx.drawImage(from, 0, 0, w, h)
      else if (to) ctx.drawImage(to, 0, 0, w, h)
      ctx.fillStyle = `rgba(255,255,255,${flash * 0.9})`
      ctx.fillRect(0, 0, w, h)
    } else if (type === 'slow_zoom') {
      const scale = 1 + t * 0.08
      if (from) {
        ctx.save()
        ctx.translate(w / 2, h / 2)
        ctx.scale(scale, scale)
        ctx.globalAlpha = 1 - t
        ctx.drawImage(from, -w / 2, -h / 2, w, h)
        ctx.restore()
      }
      if (to) { ctx.globalAlpha = t; ctx.drawImage(to, 0, 0, w, h) }
      ctx.globalAlpha = 1
    } else {
      // hard_cut
      if (t < 0.5 && from) ctx.drawImage(from, 0, 0, w, h)
      else if (to) ctx.drawImage(to, 0, 0, w, h)
    }
  }

  function drawNarrationText(ctx: CanvasRenderingContext2D, text: string, w: number, h: number) {
    if (!text) return
    ctx.save()
    ctx.font = '700 28px "Cormorant Garamond", serif'
    ctx.fillStyle = 'rgba(255,255,255,0.75)'
    ctx.textAlign = 'center'
    ctx.shadowColor = 'rgba(0,0,0,0.8)'
    ctx.shadowBlur = 12
    ctx.fillText(text, w / 2, h - 52)
    ctx.restore()
  }

  async function preloadImages(frames: ComposerFrame[]): Promise<(HTMLImageElement | null)[]> {
    return Promise.all(frames.map(f => new Promise<HTMLImageElement | null>(resolve => {
      const img = new Image()
      img.onload = () => resolve(img)
      img.onerror = () => resolve(null)
      img.src = f.image.blob_url
    })))
  }

  function nextFrame(): Promise<void> {
    return new Promise(resolve => requestAnimationFrame(() => resolve()))
  }

  return { exporting, exportProgress, exportMp4 }
}
```

- [ ] **Step 2: Build check**

```bash
npm run build -- --noEmit 2>&1 | tail -5
```

- [ ] **Step 3: Commit**

```bash
git add src/composables/useBrainExport.ts
git commit -m "Add useBrainExport MP4 pipeline composable"
```

---

## Task 7: BrainView.vue — wire everything together

**Files:**
- Create: `src/views/BrainView.vue`

- [ ] **Step 1: Create the view**

```vue
<template>
  <div class="brain-view">
    <!-- Map mode -->
    <canvas
      v-show="mode === 'map'"
      ref="mapCanvas"
      class="brain-canvas"
      @mousedown="handleMapMouseDown"
      @mousemove="handleMapMouseMove"
      @mouseup="handleMapMouseUp"
      @wheel.prevent="brainMap.onWheel"
      @click="handleMapClick"
    />

    <!-- Local mode -->
    <canvas
      v-show="mode === 'local'"
      ref="localCanvas"
      class="brain-canvas"
      @click="handleLocalClick"
    />

    <!-- Back button in local mode -->
    <button
      v-if="mode === 'local'"
      class="brain-back"
      @click="exitLocal"
    >
      ← map
    </button>

    <!-- Loading overlay -->
    <div v-if="brainMap.loading.value" class="brain-loading">
      loading library…
    </div>

    <!-- Sequence strip -->
    <div v-if="sequence.items.value.length" class="brain-strip">
      <canvas ref="curveCanvas" class="brain-curve" width="600" height="40" />
      <div class="brain-strip-items">
        <div
          v-for="(img, i) in sequence.items.value"
          :key="img.id"
          class="brain-strip-thumb"
          @click="sequence.removeAt(i)"
          :title="img.filename ?? ''"
        >
          <img :src="img.blob_url" />
          <span class="brain-strip-remove">×</span>
        </div>
      </div>
      <div class="brain-strip-actions">
        <button
          v-if="sequence.canCompose.value && !composer.generatingNarration.value"
          @click="generateNarration"
          class="brain-btn"
        >narrate</button>
        <button
          v-if="sequence.canCompose.value && !exporter.exporting.value"
          @click="doExport"
          class="brain-btn brain-btn-primary"
        >export mp4</button>
        <div v-if="exporter.exporting.value" class="brain-export-progress">
          {{ Math.round(exporter.exportProgress.value * 100) }}%
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useBrainMap } from '@/composables/useBrainMap'
import { useBrainLocal } from '@/composables/useBrainLocal'
import { useBrainSequence } from '@/composables/useBrainSequence'
import { useBrainComposer } from '@/composables/useBrainComposer'
import { useBrainExport } from '@/composables/useBrainExport'
import type { MapImage } from '@/composables/useBrainMap'

const mapCanvas = ref<HTMLCanvasElement | null>(null)
const localCanvas = ref<HTMLCanvasElement | null>(null)
const curveCanvas = ref<HTMLCanvasElement | null>(null)

const mode = ref<'map' | 'local'>('map')

const brainMap = useBrainMap(mapCanvas)
const brainLocal = useBrainLocal(localCanvas)
const sequence = useBrainSequence()
const composer = useBrainComposer()
const exporter = useBrainExport()

function resize() {
  const w = window.innerWidth
  const h = window.innerHeight
  if (mapCanvas.value) { mapCanvas.value.width = w; mapCanvas.value.height = h }
  if (localCanvas.value) { localCanvas.value.width = w; localCanvas.value.height = h }
}

onMounted(async () => {
  resize()
  window.addEventListener('resize', resize)
  brainMap.start()
  await brainMap.loadMap()
})

onUnmounted(() => {
  window.removeEventListener('resize', resize)
  brainMap.stop()
  brainLocal.stop()
  composer.stopAudio()
})

// Redraw vibe curve whenever compose result updates
watch(sequence.compose, () => {
  if (curveCanvas.value) sequence.drawVibeCurve(curveCanvas.value)
})

// ── Map interactions ──────────────────────────────────────────────────────────

function handleMapMouseDown(e: MouseEvent) {
  brainMap.onMouseDown(e)
}

function handleMapMouseMove(e: MouseEvent) {
  brainMap.onMouseMove(e)
}

function handleMapMouseUp(e: MouseEvent) {
  brainMap.onMouseUp(e)
}

function handleMapClick(e: MouseEvent) {
  const wasTap = brainMap.onMouseUp(e)
  if (!wasTap || !mapCanvas.value) return
  const rect = mapCanvas.value.getBoundingClientRect()
  const sx = e.clientX - rect.left
  const sy = e.clientY - rect.top
  const img = brainMap.hitTest(sx, sy, mapCanvas.value)
  if (img) enterLocal(img)
}

// ── Local interactions ────────────────────────────────────────────────────────

async function enterLocal(img: MapImage) {
  brainMap.stop()
  mode.value = 'local'
  brainLocal.start()
  await brainLocal.setFocal(img)
}

function exitLocal() {
  brainLocal.stop()
  mode.value = 'map'
  brainMap.start()
}

function handleLocalClick(e: MouseEvent) {
  if (!localCanvas.value) return
  const rect = localCanvas.value.getBoundingClientRect()
  const sx = e.clientX - rect.left
  const sy = e.clientY - rect.top
  const neighbor = brainLocal.hitTestNeighbor(sx, sy)
  if (!neighbor) return
  // Add focal image to sequence, then traverse to neighbor
  const focal = brainLocal.focal.value
  if (focal) {
    sequence.addImage(focal)
    brainMap.markVisited(focal.id)
  }
  brainLocal.setFocal(neighbor.image)
  composer.startAudio(sequence.compose.value)
}

// ── Composer actions ──────────────────────────────────────────────────────────

async function generateNarration() {
  await composer.generateNarration(sequence.items.value, sequence.compose.value)
}

async function doExport() {
  const frames = composer.buildFrames(sequence.items.value, sequence.compose.value)
  await exporter.exportMp4(
    frames,
    composer.narration.value,
    composer.drawGeometry,
  )
}
</script>

<style scoped>
.brain-view {
  position: fixed;
  inset: 0;
  background: #0a0a0f;
  overflow: hidden;
  user-select: none;
}

.brain-canvas {
  position: absolute;
  inset: 0;
  cursor: crosshair;
}

.brain-back {
  position: absolute;
  top: 20px;
  left: 20px;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.12);
  color: rgba(255,255,255,0.7);
  font-size: 13px;
  padding: 6px 14px;
  border-radius: 6px;
  cursor: pointer;
  letter-spacing: 0.05em;
  z-index: 10;
}

.brain-back:hover { background: rgba(255,255,255,0.1); }

.brain-loading {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255,255,255,0.3);
  font-size: 13px;
  letter-spacing: 0.1em;
  pointer-events: none;
}

.brain-strip {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(0,0,0,0.75);
  backdrop-filter: blur(12px);
  border-top: 1px solid rgba(255,255,255,0.06);
  padding: 8px 12px 12px;
  z-index: 20;
}

.brain-curve {
  width: 100%;
  height: 40px;
  display: block;
  margin-bottom: 6px;
  opacity: 0.8;
}

.brain-strip-items {
  display: flex;
  gap: 6px;
  overflow-x: auto;
  padding-bottom: 6px;
}

.brain-strip-thumb {
  position: relative;
  flex-shrink: 0;
  width: 52px;
  height: 52px;
  border-radius: 6px;
  overflow: hidden;
  cursor: pointer;
  border: 1px solid rgba(255,255,255,0.1);
}

.brain-strip-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.brain-strip-remove {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0,0,0,0.6);
  color: white;
  font-size: 18px;
  opacity: 0;
  transition: opacity 0.15s;
}

.brain-strip-thumb:hover .brain-strip-remove { opacity: 1; }

.brain-strip-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
  align-items: center;
}

.brain-btn {
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  padding: 5px 12px;
  border-radius: 5px;
  border: 1px solid rgba(255,255,255,0.15);
  background: rgba(255,255,255,0.05);
  color: rgba(255,255,255,0.7);
  cursor: pointer;
}

.brain-btn:hover { background: rgba(255,255,255,0.1); }

.brain-btn-primary {
  border-color: rgba(139,92,246,0.5);
  color: #a78bfa;
}

.brain-export-progress {
  font-size: 11px;
  color: rgba(139,92,246,0.8);
  letter-spacing: 0.08em;
}
</style>
```

- [ ] **Step 2: Build check — full TypeScript compile**

```bash
npm run build 2>&1 | tail -20
```

Expected: build completes with no TypeScript errors.

- [ ] **Step 3: Dev server smoke test**

```bash
npm run dev &
sleep 4
open http://localhost:5173/brain
```

Expected: `/brain` loads, dark canvas renders, no console errors.

- [ ] **Step 4: Commit**

```bash
git add src/views/BrainView.vue
git commit -m "Add BrainView — spatial image map, local traversal, sequence strip, export"
```

- [ ] **Step 5: Push and verify Vercel deploy**

```bash
git push origin main
```

Check Vercel dashboard — build should pass. Navigate to `channelzero.vercel.app/brain` and confirm the view loads.
