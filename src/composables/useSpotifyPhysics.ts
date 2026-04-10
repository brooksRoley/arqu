import { ref, readonly, type Ref } from 'vue'
import { useCosmicPhysics, DEFAULT_ORB_DEFS, type OrbDef } from './useCosmicPhysics'

// ── Types ────────────────────────────────────────────────────────────────────

export interface SpotifyPhysicsProfile {
  top_artists: string[]
  genres: string[]
  audio_avg: {
    valence?: number
    danceability?: number
    energy?: number
    acousticness?: number
    instrumentalness?: number
    tempo?: number
  }
}

export interface AudioSummary {
  valence: number
  energy: number
  danceability: number
  acousticness: number
  tempo: number
}

// ── Genre → color mapping ────────────────────────────────────────────────────
// Maps broad genre family keywords to a characteristic hue

function genreToColor(genre: string): OrbDef {
  const g = genre.toLowerCase()
  if (/electr|techno|house|dance|edm|synth|drum/.test(g))  return { r: 0,   g: 195, b: 220 }
  if (/hip.?hop|rap|trap/.test(g))                          return { r: 230, g: 160, b: 30  }
  if (/r&b|rnb|soul|neo.?soul/.test(g))                     return { r: 200, g: 100, b: 60  }
  if (/rock|metal|punk|grunge|hard/.test(g))                return { r: 210, g: 50,  b: 50  }
  if (/pop|teen|mainstream/.test(g))                        return { r: 220, g: 80,  b: 160 }
  if (/indie|alternative|lo.?fi|bedroom/.test(g))           return { r: 130, g: 80,  b: 220 }
  if (/jazz|blues/.test(g))                                 return { r: 200, g: 140, b: 30  }
  if (/classical|orchestral|chamber/.test(g))               return { r: 50,  g: 175, b: 130 }
  if (/ambient|atmospheric|drone|shoegaze|post/.test(g))    return { r: 60,  g: 130, b: 200 }
  if (/folk|country|bluegrass|americana/.test(g))           return { r: 175, g: 125, b: 55  }
  if (/latin|reggaeton|salsa|cumbia/.test(g))               return { r: 210, g: 90,  b: 30  }
  if (/k.?pop|j.?pop|city.?pop/.test(g))                   return { r: 255, g: 100, b: 150 }
  return { r: 123, g: 94, b: 167 }
}

// ── Canvas helper: rounded rect path ────────────────────────────────────────

function rrect(
  ctx: CanvasRenderingContext2D,
  x: number, y: number, w: number, h: number, r: number,
) {
  ctx.beginPath()
  ctx.moveTo(x + r, y)
  ctx.lineTo(x + w - r, y)
  ctx.arcTo(x + w, y, x + w, y + r, r)
  ctx.lineTo(x + w, y + h - r)
  ctx.arcTo(x + w, y + h, x + w - r, y + h, r)
  ctx.lineTo(x + r, y + h)
  ctx.arcTo(x, y + h, x, y + h - r, r)
  ctx.lineTo(x, y + r)
  ctx.arcTo(x, y, x + r, y, r)
  ctx.closePath()
}

// ── Composable ───────────────────────────────────────────────────────────────

export function useSpotifyPhysics(
  cosmicCanvas: Ref<HTMLCanvasElement | undefined>,
  overlayCanvas: Ref<HTMLCanvasElement | undefined>,
  profile: SpotifyPhysicsProfile,
) {
  const audio = profile.audio_avg ?? {}
  const energy      = audio.energy      ?? 0.5
  const acousticness = audio.acousticness ?? 0.5
  const valence     = audio.valence     ?? 0.5
  const tempo       = audio.tempo       ?? 120
  const danceability = audio.danceability ?? 0.5

  // ── Derive orb palette from top genres ───────────────────────────
  const topGenres = profile.genres.slice(0, 6)
  const orbDefs: OrbDef[] = topGenres.length > 0
    ? topGenres.map(genreToColor)
    : DEFAULT_ORB_DEFS.slice(0, 4)

  // ── Assign artists to orbs round-robin ───────────────────────────
  const artistsByOrb: Record<number, string[]> = {}
  profile.top_artists.forEach((artist, i) => {
    const idx = i % orbDefs.length
    if (!artistsByOrb[idx]) artistsByOrb[idx] = []
    artistsByOrb[idx].push(artist)
  })

  // ── Wire useCosmicPhysics with audio-derived params ──────────────
  // energy       → particle density + mouse force
  // acousticness → trail persistence (acoustic = softer, slower fade)
  // tempo        → normalised to clearAlpha nudge (high BPM = crisper)
  const normTempo = Math.min(1, Math.max(0, (tempo - 60) / 140))
  const cosmic = useCosmicPhysics(cosmicCanvas, {
    orbDefs,
    particleCount: Math.round(80 + energy * 160),
    starCount: 120,
    clearAlpha: 0.055 + (1 - acousticness) * 0.04 + normTempo * 0.02,
    enableKeyboard: false,
    enableMouseInteract: true,
    mouseAttractForce: 0.25 + energy * 0.6,
  })

  // ── Overlay state ─────────────────────────────────────────────────
  const hoveredIdx = ref<number | null>(null)

  let overlayRaf = 0
  let overlayCtx: CanvasRenderingContext2D | null = null
  let W = 0, H = 0, dpr = 1
  let mx = 0, my = 0

  function resizeOverlay() {
    const c = overlayCanvas.value; if (!c) return
    dpr = Math.min(window.devicePixelRatio || 1, 2)
    W = c.clientWidth; H = c.clientHeight
    c.width = W * dpr; c.height = H * dpr
    overlayCtx = c.getContext('2d')!
    overlayCtx.setTransform(dpr, 0, 0, dpr, 0, 0)
  }

  // ── Valence gradient field ────────────────────────────────────────
  // High valence → warm amber edge wash; low valence → cool blue wash; mid → neutral
  function drawValenceField() {
    if (!overlayCtx) return
    const warmR = Math.round(valence * 200)
    const warmG = Math.round(valence * 70)
    const warmB = Math.round((1 - valence) * 190)
    const alpha = 0.025 + Math.abs(valence - 0.5) * 0.055

    const grad = overlayCtx.createRadialGradient(
      W * 0.5, H * 0.5, H * 0.12,
      W * 0.5, H * 0.5, H * 0.8,
    )
    grad.addColorStop(0, `rgba(${warmR},${warmG},${warmB},0)`)
    grad.addColorStop(1, `rgba(${warmR},${warmG},${warmB},${alpha})`)
    overlayCtx.fillStyle = grad
    overlayCtx.fillRect(0, 0, W, H)
  }

  // ── Per-orb genre label + artist expansion on hover ───────────────
  function drawOrbLabel(
    x: number, y: number, idx: number,
    genre: string, color: OrbDef, isHovered: boolean,
  ) {
    if (!overlayCtx || !genre) return
    const ctx = overlayCtx
    const { r, g, b } = color
    const labelAlpha = isHovered ? 1 : 0.65

    // ── Genre pill ──
    ctx.font = isHovered ? 'bold 11px monospace' : '10px monospace'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    const tw = ctx.measureText(genre).width
    const pillW = tw + 18
    const pillH = 18
    const pillX = x - pillW / 2
    const pillY = y + 28

    ctx.fillStyle = `rgba(8,6,14,0.72)`
    rrect(ctx, pillX, pillY, pillW, pillH, 5)
    ctx.fill()

    ctx.fillStyle = `rgba(${r},${g},${b},${labelAlpha})`
    ctx.fillText(genre, x, pillY + pillH / 2)

    // ── Artist list (hover only) ──
    if (isHovered) {
      const artists = artistsByOrb[idx] ?? []
      let ay = pillY + pillH + 6
      for (const artist of artists) {
        ctx.font = '9px monospace'
        const aw = ctx.measureText(artist).width + 14
        ctx.fillStyle = `rgba(8,6,14,0.6)`
        rrect(ctx, x - aw / 2, ay, aw, 14, 3)
        ctx.fill()
        ctx.fillStyle = `rgba(200,190,230,0.9)`
        ctx.fillText(artist, x, ay + 7)
        ay += 17
      }
    }
  }

  // ── Overlay frame loop ────────────────────────────────────────────
  function frameOverlay() {
    if (!overlayCtx) { overlayRaf = requestAnimationFrame(frameOverlay); return }
    overlayCtx.clearRect(0, 0, W, H)

    drawValenceField()

    const positions = cosmic.getOrbPositions()

    // Update hover nearest-orb
    let nearest: number | null = null
    let nearestDist = 58
    for (const { x, y, idx } of positions) {
      const d = Math.hypot(x - mx, y - my)
      if (d < nearestDist) { nearestDist = d; nearest = idx }
    }
    hoveredIdx.value = nearest

    // Draw labels
    for (const { x, y, idx } of positions) {
      const genre = topGenres[idx] ?? ''
      const color = orbDefs[idx] ?? { r: 160, g: 140, b: 220 }
      drawOrbLabel(x, y, idx, genre, color, hoveredIdx.value === idx)
    }

    overlayRaf = requestAnimationFrame(frameOverlay)
  }

  // ── Mouse tracking on overlay canvas ─────────────────────────────
  function _onMouseMove(e: MouseEvent) {
    const c = overlayCanvas.value; if (!c) return
    const rect = c.getBoundingClientRect()
    mx = e.clientX - rect.left
    my = e.clientY - rect.top
  }

  function _onClick(e: MouseEvent) {
    const c = overlayCanvas.value; if (!c) return
    const rect = c.getBoundingClientRect()
    cosmic.clickImpulse(e.clientX - rect.left, e.clientY - rect.top)
  }

  // ── Lifecycle ─────────────────────────────────────────────────────

  async function init() {
    const ok = await cosmic.init()
    if (!ok) return false
    resizeOverlay()
    window.addEventListener('resize', resizeOverlay)
    const c = overlayCanvas.value
    if (c) {
      c.addEventListener('mousemove', _onMouseMove)
      c.addEventListener('click', _onClick)
    }
    overlayRaf = requestAnimationFrame(frameOverlay)
    return true
  }

  function destroy() {
    cosmic.destroy()
    if (overlayRaf) cancelAnimationFrame(overlayRaf)
    window.removeEventListener('resize', resizeOverlay)
    const c = overlayCanvas.value
    if (c) {
      c.removeEventListener('mousemove', _onMouseMove)
      c.removeEventListener('click', _onClick)
    }
  }

  // ── Exports ───────────────────────────────────────────────────────

  const audioSummary: AudioSummary = {
    valence,
    energy,
    danceability,
    acousticness,
    tempo: Math.round(tempo),
  }

  return {
    loaded: cosmic.loaded,
    adapt: cosmic.adapt,
    init,
    destroy,
    heatOrb: cosmic.heatOrb,
    hoveredIdx: readonly(hoveredIdx),
    topGenres,
    orbDefs,
    audioSummary,
  }
}
