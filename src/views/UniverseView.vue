<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/composables/useAuthStore'
import { usePollStore } from '@/composables/usePollStore'
import { useVibeStore } from '@/composables/useVibeStore'

const router = useRouter()
const { user, isAuthenticated } = useAuthStore()
const { token: pollToken } = usePollStore()
const { oauthState } = useVibeStore()

if (!isAuthenticated.value) router.replace('/login')

const canvas = ref<HTMLCanvasElement>()
let animId: number | null = null

// ── Planet definitions ──────────────────────────────────────────────

interface Planet {
  key: string
  label: string
  sublabel: string
  radius: number        // visual radius
  orbitRadius: number   // distance from center
  speed: number         // radians per frame
  angle: number         // current angle
  color: string
  glowColor: string
  importance: number    // 0-1, affects brightness + ring thickness
  warning: string | null
  pulse: number         // animation counter
}

const accent = computed(() => pollToken.value?.palette?.accent || '#a78bfa')

function buildPlanets(): Planet[] {
  const hasSpotify = oauthState.value.spotify.connected
  const hasTwitter = oauthState.value.twitter.connected
  const hasPoll = !!pollToken.value
  const connectedCount = [hasSpotify, hasTwitter].filter(Boolean).length

  return [
    {
      key: 'identity',
      label: 'Identity',
      sublabel: hasPoll ? (pollToken.value?.archetype || 'Unknown') : 'Take the poll',
      radius: 28,
      orbitRadius: 0, // center "sun"
      speed: 0,
      angle: 0,
      color: accent.value,
      glowColor: accent.value,
      importance: hasPoll ? 0.9 : 0.3,
      warning: hasPoll ? null : 'Uncalibrated',
      pulse: 0,
    },
    {
      key: 'sonic',
      label: 'Sonic Blueprint',
      sublabel: hasSpotify ? 'Synced' : 'Connect Spotify',
      radius: 18,
      orbitRadius: 100,
      speed: 0.004,
      angle: Math.random() * Math.PI * 2,
      color: '#1DB954',
      glowColor: '#1DB954',
      importance: hasSpotify ? 0.85 : 0.2,
      warning: hasSpotify ? null : 'No signal',
      pulse: 0,
    },
    {
      key: 'social',
      label: 'Social Imprint',
      sublabel: hasTwitter ? 'Synced' : 'Connect X',
      radius: 15,
      orbitRadius: 155,
      speed: 0.003,
      angle: Math.random() * Math.PI * 2,
      color: '#3b82f6',
      glowColor: '#60a5fa',
      importance: hasTwitter ? 0.8 : 0.2,
      warning: hasTwitter ? null : 'No signal',
      pulse: 0,
    },
    {
      key: 'psyche',
      label: 'Psyche',
      sublabel: 'Analysis engine',
      radius: 20,
      orbitRadius: 210,
      speed: 0.002,
      angle: Math.random() * Math.PI * 2,
      color: '#c084fc',
      glowColor: '#a855f7',
      importance: hasPoll ? 0.7 : 0.15,
      warning: hasPoll ? null : 'Dormant',
      pulse: 0,
    },
    {
      key: 'shadow',
      label: 'Shadow',
      sublabel: 'Unconscious patterns',
      radius: 14,
      orbitRadius: 265,
      speed: 0.0015,
      angle: Math.random() * Math.PI * 2,
      color: '#475569',
      glowColor: '#64748b',
      importance: 0.5,
      warning: connectedCount < 2 ? 'Insufficient data' : null,
      pulse: 0,
    },
    {
      key: 'connections',
      label: 'Connections',
      sublabel: 'Match readiness',
      radius: 12,
      orbitRadius: 315,
      speed: 0.001,
      angle: Math.random() * Math.PI * 2,
      color: '#f59e0b',
      glowColor: '#fbbf24',
      importance: connectedCount >= 1 ? 0.6 : 0.1,
      warning: connectedCount === 0 ? 'Offline' : null,
      pulse: 0,
    },
  ]
}

const planets = ref<Planet[]>(buildPlanets())

// ── Stars background ────────────────────────────────────────────────

interface Star {
  x: number
  y: number
  r: number
  alpha: number
  twinkleSpeed: number
  twinklePhase: number
}

let stars: Star[] = []

function generateStars(w: number, h: number) {
  stars = []
  const count = Math.floor((w * h) / 3000)
  for (let i = 0; i < count; i++) {
    stars.push({
      x: Math.random() * w,
      y: Math.random() * h,
      r: Math.random() * 1.2 + 0.3,
      alpha: Math.random() * 0.5 + 0.3,
      twinkleSpeed: Math.random() * 0.02 + 0.005,
      twinklePhase: Math.random() * Math.PI * 2,
    })
  }
}

// ── Render loop ─────────────────────────────────────────────────────

let frameCount = 0
let hoveredPlanet: Planet | null = null
let mouseX = 0
let mouseY = 0

function render() {
  const c = canvas.value
  if (!c) return
  const ctx = c.getContext('2d')
  if (!ctx) return

  const w = c.width
  const h = c.height
  const cx = w / 2
  const cy = h / 2

  frameCount++

  // Clear
  ctx.fillStyle = '#05050f'
  ctx.fillRect(0, 0, w, h)

  // Subtle radial gradient background
  const bg = ctx.createRadialGradient(cx, cy, 0, cx, cy, Math.max(w, h) * 0.5)
  bg.addColorStop(0, 'rgba(15, 15, 40, 0.6)')
  bg.addColorStop(1, 'rgba(5, 5, 15, 0)')
  ctx.fillStyle = bg
  ctx.fillRect(0, 0, w, h)

  // Stars
  for (const s of stars) {
    const flicker = Math.sin(frameCount * s.twinkleSpeed + s.twinklePhase) * 0.3 + 0.7
    ctx.beginPath()
    ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2)
    ctx.fillStyle = `rgba(200, 210, 255, ${s.alpha * flicker})`
    ctx.fill()
  }

  // Orbit rings
  for (const p of planets.value) {
    if (p.orbitRadius === 0) continue
    ctx.beginPath()
    ctx.arc(cx, cy, p.orbitRadius, 0, Math.PI * 2)
    ctx.strokeStyle = `rgba(255, 255, 255, 0.04)`
    ctx.lineWidth = 1
    ctx.stroke()
  }

  // Update + draw planets
  for (const p of planets.value) {
    p.angle += p.speed
    p.pulse++

    const px = p.orbitRadius === 0 ? cx : cx + Math.cos(p.angle) * p.orbitRadius
    const py = p.orbitRadius === 0 ? cy : cy + Math.sin(p.angle) * p.orbitRadius * 0.55 // elliptical

    // Glow
    const glowSize = p.radius * (2 + p.importance)
    const glow = ctx.createRadialGradient(px, py, p.radius * 0.5, px, py, glowSize)
    const alpha = 0.15 + p.importance * 0.2
    glow.addColorStop(0, p.glowColor + hexAlpha(alpha))
    glow.addColorStop(1, p.glowColor + '00')
    ctx.beginPath()
    ctx.arc(px, py, glowSize, 0, Math.PI * 2)
    ctx.fillStyle = glow
    ctx.fill()

    // Planet body
    const bodyGrad = ctx.createRadialGradient(
      px - p.radius * 0.3, py - p.radius * 0.3, p.radius * 0.1,
      px, py, p.radius,
    )
    bodyGrad.addColorStop(0, lighten(p.color, 40))
    bodyGrad.addColorStop(0.7, p.color)
    bodyGrad.addColorStop(1, darken(p.color, 30))
    ctx.beginPath()
    ctx.arc(px, py, p.radius, 0, Math.PI * 2)
    ctx.fillStyle = bodyGrad
    ctx.fill()

    // Importance ring
    if (p.importance > 0.5) {
      ctx.beginPath()
      ctx.arc(px, py, p.radius + 4, 0, Math.PI * 2 * p.importance)
      ctx.strokeStyle = p.color + '88'
      ctx.lineWidth = 2
      ctx.stroke()
    }

    // Warning indicator
    if (p.warning) {
      const pulseAlpha = Math.sin(p.pulse * 0.06) * 0.4 + 0.6
      const warnX = px + p.radius * 0.7
      const warnY = py - p.radius * 0.7

      // Warning dot
      ctx.beginPath()
      ctx.arc(warnX, warnY, 5, 0, Math.PI * 2)
      ctx.fillStyle = `rgba(251, 191, 36, ${pulseAlpha})`
      ctx.fill()

      // Warning pulse ring
      const ringSize = 5 + (p.pulse % 60) / 60 * 10
      ctx.beginPath()
      ctx.arc(warnX, warnY, ringSize, 0, Math.PI * 2)
      ctx.strokeStyle = `rgba(251, 191, 36, ${0.6 - (p.pulse % 60) / 60 * 0.6})`
      ctx.lineWidth = 1
      ctx.stroke()
    }

    // Label
    const isHovered = hoveredPlanet === p
    const labelAlpha = p.orbitRadius === 0 ? 1 : (isHovered ? 1 : 0.7)
    ctx.font = `${isHovered ? 600 : 500} ${p.orbitRadius === 0 ? 14 : 11}px Inter, system-ui, sans-serif`
    ctx.fillStyle = `rgba(255, 255, 255, ${labelAlpha})`
    ctx.textAlign = 'center'
    ctx.fillText(p.label, px, py + p.radius + 18)

    // Sublabel
    ctx.font = `400 ${p.orbitRadius === 0 ? 11 : 9}px Inter, system-ui, sans-serif`
    ctx.fillStyle = p.warning
      ? `rgba(251, 191, 36, ${labelAlpha * 0.9})`
      : `rgba(160, 180, 220, ${labelAlpha * 0.7})`
    ctx.fillText(p.sublabel, px, py + p.radius + 32)

    // Warning text
    if (p.warning && isHovered) {
      ctx.font = '500 10px Inter, system-ui, sans-serif'
      ctx.fillStyle = 'rgba(251, 191, 36, 0.9)'
      ctx.fillText(p.warning, px, py + p.radius + 44)
    }
  }

  // Title text at top
  ctx.font = '600 13px Inter, system-ui, sans-serif'
  ctx.fillStyle = 'rgba(255, 255, 255, 0.3)'
  ctx.textAlign = 'center'
  ctx.fillText('YOUR UNIVERSE', cx, 30)

  animId = requestAnimationFrame(render)
}

// ── Helpers ─────────────────────────────────────────────────────────

function hexAlpha(a: number): string {
  return Math.round(Math.min(1, Math.max(0, a)) * 255).toString(16).padStart(2, '0')
}

function lighten(hex: string, pct: number): string {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  const f = pct / 100
  return `rgb(${Math.min(255, r + (255 - r) * f)}, ${Math.min(255, g + (255 - g) * f)}, ${Math.min(255, b + (255 - b) * f)})`
}

function darken(hex: string, pct: number): string {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  const f = 1 - pct / 100
  return `rgb(${Math.round(r * f)}, ${Math.round(g * f)}, ${Math.round(b * f)})`
}

// ── Hit detection ───────────────────────────────────────────────────

function findPlanetAt(mx: number, my: number): Planet | null {
  const c = canvas.value
  if (!c) return null
  const cx = c.width / 2
  const cy = c.height / 2

  for (const p of planets.value) {
    const px = p.orbitRadius === 0 ? cx : cx + Math.cos(p.angle) * p.orbitRadius
    const py = p.orbitRadius === 0 ? cy : cy + Math.sin(p.angle) * p.orbitRadius * 0.55
    const dx = mx - px
    const dy = my - py
    if (Math.sqrt(dx * dx + dy * dy) < p.radius + 10) return p
  }
  return null
}

function onMouseMove(e: MouseEvent) {
  const c = canvas.value
  if (!c) return
  const r = c.getBoundingClientRect()
  const scaleX = c.width / r.width
  const scaleY = c.height / r.height
  mouseX = (e.clientX - r.left) * scaleX
  mouseY = (e.clientY - r.top) * scaleY
  hoveredPlanet = findPlanetAt(mouseX, mouseY)
  c.style.cursor = hoveredPlanet ? 'pointer' : 'default'
}

function onClick(e: MouseEvent) {
  const c = canvas.value
  if (!c) return
  const r = c.getBoundingClientRect()
  const scaleX = c.width / r.width
  const scaleY = c.height / r.height
  const mx = (e.clientX - r.left) * scaleX
  const my = (e.clientY - r.top) * scaleY
  const p = findPlanetAt(mx, my)
  if (!p) return

  const routes: Record<string, string> = {
    identity: '/',
    sonic: '/calibrate',
    social: '/calibrate',
    psyche: '/psychoanalysis',
    shadow: '/intake',
    connections: '/game',
  }
  if (routes[p.key]) router.push(routes[p.key])
}

// ── Resize ──────────────────────────────────────────────────────────

function resize() {
  const c = canvas.value
  if (!c) return
  const dpr = window.devicePixelRatio || 1
  const parent = c.parentElement!
  c.width = parent.clientWidth * dpr
  c.height = parent.clientHeight * dpr
  c.style.width = parent.clientWidth + 'px'
  c.style.height = parent.clientHeight + 'px'

  // Scale orbit radii for smaller screens
  const scale = Math.min(c.width, c.height) / 800
  const baseRadii = [0, 100, 155, 210, 265, 315]
  planets.value.forEach((p, i) => {
    p.orbitRadius = baseRadii[i] * Math.max(0.5, scale)
    p.radius = [28, 18, 15, 20, 14, 12][i] * Math.max(0.6, Math.min(1, scale))
  })

  generateStars(c.width, c.height)
}

// ── Lifecycle ───────────────────────────────────────────────────────

onMounted(() => {
  resize()
  window.addEventListener('resize', resize)
  canvas.value?.addEventListener('mousemove', onMouseMove)
  canvas.value?.addEventListener('click', onClick)
  render()
})

onUnmounted(() => {
  if (animId) cancelAnimationFrame(animId)
  window.removeEventListener('resize', resize)
  canvas.value?.removeEventListener('mousemove', onMouseMove)
  canvas.value?.removeEventListener('click', onClick)
})

// ── Navigation ──────────────────────────────────────────────────────

const displayName = computed(() => user.value?.display_name || user.value?.email?.split('@')[0] || 'Explorer')

function startJourney() {
  if (!pollToken.value) {
    router.push('/')
  } else {
    router.push('/calibrate')
  }
}
</script>

<template>
  <div class="universe-wrap">
    <canvas ref="canvas" class="universe-canvas"></canvas>

    <!-- Welcome overlay -->
    <div class="welcome-overlay">
      <h1 class="welcome-title">Welcome, {{ displayName }}</h1>
      <p class="welcome-sub">Your universe is forming. Each planet represents a dimension of your signal.</p>

      <div class="planet-legend">
        <div
          v-for="p in planets"
          :key="p.key"
          class="legend-item"
          :class="{ 'legend-item--warn': p.warning }"
        >
          <span class="legend-dot" :style="{ background: p.color }"></span>
          <span class="legend-name">{{ p.label }}</span>
          <span v-if="p.warning" class="legend-warn">{{ p.warning }}</span>
          <span v-else class="legend-ok">Active</span>
        </div>
      </div>

      <button class="universe-cta" :style="{ background: accent }" @click="startJourney">
        Begin Calibration
      </button>

      <button class="universe-skip" @click="router.push('/')">
        Explore on your own
      </button>
    </div>
  </div>
</template>

<style scoped>
.universe-wrap {
  position: relative;
  width: 100%;
  height: 100vh;
  overflow: hidden;
  background: #05050f;
}

.universe-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

/* ── Welcome overlay ── */
.welcome-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 2rem 2rem 3rem;
  background: linear-gradient(to top, rgba(5, 5, 15, 0.95) 0%, rgba(5, 5, 15, 0.7) 60%, transparent 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  z-index: 10;
}

.welcome-title {
  font-size: 1.6rem;
  font-weight: 700;
  color: #e2e8f0;
  margin: 0;
  letter-spacing: -0.02em;
}

.welcome-sub {
  font-size: 0.85rem;
  color: #64748b;
  margin: 0;
  text-align: center;
  max-width: 400px;
  line-height: 1.6;
}

/* ── Planet legend ── */
.planet-legend {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.5rem 1rem;
  margin: 0.5rem 0;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.72rem;
  color: #94a3b8;
}

.legend-item--warn { color: #fbbf24; }

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.legend-name { font-weight: 500; }

.legend-warn {
  font-size: 0.62rem;
  color: #fbbf24;
  background: rgba(251, 191, 36, 0.1);
  padding: 0.1rem 0.4rem;
  border-radius: 100px;
}

.legend-ok {
  font-size: 0.62rem;
  color: #22c55e;
  background: rgba(34, 197, 94, 0.1);
  padding: 0.1rem 0.4rem;
  border-radius: 100px;
}

/* ── CTAs ── */
.universe-cta {
  padding: 0.75rem 2rem;
  border: none;
  border-radius: 0.5rem;
  color: #0f0f1a;
  font-size: 0.9rem;
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
  transition: opacity 0.15s, transform 0.1s;
  margin-top: 0.25rem;
}

.universe-cta:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

.universe-skip {
  background: none;
  border: none;
  color: #475569;
  font-size: 0.75rem;
  font-family: inherit;
  cursor: pointer;
  padding: 0.3rem 0;
  transition: color 0.15s;
}

.universe-skip:hover { color: #94a3b8; }

@media (max-width: 600px) {
  .welcome-overlay { padding: 1.5rem 1rem 2rem; }
  .welcome-title { font-size: 1.3rem; }
  .planet-legend { gap: 0.4rem 0.6rem; }
}
</style>
