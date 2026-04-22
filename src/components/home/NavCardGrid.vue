<script setup lang="ts">
import { reactive } from 'vue'

const props = defineProps<{
  getOrbPositions?: () => { x: number; y: number; idx: number }[]
  heatOrb?: (idx: number, amount?: number) => void
}>()

const emit = defineEmits<{
  (e: 'open-meditation'): void
}>()

// ── Per-card 3D tilt ─────────────────────────────────────────────
const cardTilts = reactive(
  new Map<string, { tx: number; ty: number; gx: number; gy: number; hover: boolean }>()
)

function getTilt(key: string) {
  if (!cardTilts.has(key)) {
    cardTilts.set(key, { tx: 0, ty: 0, gx: 50, gy: 50, hover: false })
  }
  return cardTilts.get(key)!
}

function onCardMove(e: PointerEvent, key: string) {
  const el = e.currentTarget as HTMLElement
  const r = el.getBoundingClientRect()
  const nx = ((e.clientX - r.left) / r.width) * 2 - 1
  const ny = ((e.clientY - r.top) / r.height) * 2 - 1
  const c = getTilt(key)
  c.tx = ny * -5
  c.ty = nx * 5
  c.gx = (nx + 1) * 50
  c.gy = (ny + 1) * 50
}

function onCardEnter(e: PointerEvent, key: string) {
  getTilt(key).hover = true
  // Heat the nearest physics orb to this card
  if (props.getOrbPositions && props.heatOrb) {
    const el = e.currentTarget as HTMLElement
    const r = el.getBoundingClientRect()
    const cx = r.left + r.width / 2
    const cy = r.top + r.height / 2
    const orbs = props.getOrbPositions()
    let nearest = 0, bestDist = Infinity
    for (const o of orbs) {
      const d = Math.hypot(o.x - cx, o.y - cy)
      if (d < bestDist) { bestDist = d; nearest = o.idx }
    }
    props.heatOrb(nearest, 0.6)
  }
}

function onCardLeave(key: string) {
  const c = getTilt(key)
  c.tx = 0; c.ty = 0; c.gx = 50; c.gy = 50; c.hover = false
}

function cardStyle(key: string) {
  const c = getTilt(key)
  return {
    transform: `perspective(600px) rotateX(${c.tx}deg) rotateY(${c.ty}deg)`,
    '--gx': `${c.gx}%`,
    '--gy': `${c.gy}%`,
    transition: c.hover
      ? 'box-shadow 0.2s ease'
      : 'transform 0.6s cubic-bezier(0.23, 1, 0.32, 1), box-shadow 0.2s ease',
  }
}
</script>

<template>
  <div class="nav-grid">
    <router-link
      to="/checkin"
      class="nav-card nav-card--pipeline"
      :style="cardStyle('checkin')"
      @pointermove="onCardMove($event, 'checkin')"
      @pointerenter="onCardEnter($event, 'checkin')"
      @pointerleave="onCardLeave('checkin')"
    >
      <span class="card-title">Check-In</span>
      <span class="card-desc">Journal, intake, and the game — your daily pipeline</span>
      <div class="card-glare"></div>
    </router-link>

    <router-link
      to="/journal"
      class="nav-card"
      :style="cardStyle('journal')"
      @pointermove="onCardMove($event, 'journal')"
      @pointerenter="onCardEnter($event, 'journal')"
      @pointerleave="onCardLeave('journal')"
    >
      <span class="card-title">Journal</span>
      <span class="card-desc">Write, draw, record — reflective journaling with TTS</span>
      <div class="card-glare"></div>
    </router-link>

    <div
      class="nav-card nav-card--meditation"
      :style="cardStyle('meditation')"
      @pointermove="onCardMove($event, 'meditation')"
      @pointerenter="onCardEnter($event, 'meditation')"
      @pointerleave="onCardLeave('meditation')"
      @click="emit('open-meditation')"
    >
      <span class="card-title">Meditation</span>
      <span class="card-desc">Guided affirmations with gentle music and nature sounds</span>
      <div class="card-glare"></div>
    </div>

    <router-link
      to="/reader"
      class="nav-card"
      :style="cardStyle('reader')"
      @pointermove="onCardMove($event, 'reader')"
      @pointerenter="onCardEnter($event, 'reader')"
      @pointerleave="onCardLeave('reader')"
    >
      <span class="card-title">Reader</span>
      <span class="card-desc">Speed-read through uploaded stories and text</span>
      <div class="card-glare"></div>
    </router-link>

    <router-link
      to="/audio"
      class="nav-card"
      :style="cardStyle('audio')"
      @pointermove="onCardMove($event, 'audio')"
      @pointerenter="onCardEnter($event, 'audio')"
      @pointerleave="onCardLeave('audio')"
    >
      <span class="card-title">Audio</span>
      <span class="card-desc">Browse and play background audio tracks</span>
      <div class="card-glare"></div>
    </router-link>

    <router-link
      to="/studio"
      class="nav-card"
      :style="cardStyle('glass')"
      @pointermove="onCardMove($event, 'glass')"
      @pointerenter="onCardEnter($event, 'glass')"
      @pointerleave="onCardLeave('glass')"
    >
      <span class="card-title">Glass Studio</span>
      <span class="card-desc">Upload media, layer binaural tones, add text overlays</span>
      <div class="card-glare"></div>
    </router-link>
  </div>
</template>

<style scoped>
.nav-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.25rem;
}

.nav-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  padding: 2rem 1.5rem;
  min-height: 120px;
  background: rgba(15, 12, 28, 0.25);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 1rem;
  backdrop-filter: blur(6px);
  text-decoration: none;
  color: #e2e8f0;
  position: relative;
  overflow: hidden;
  will-change: transform;
  cursor: pointer;
  transition: border-color 0.3s, box-shadow 0.3s, background 0.3s;
}

.nav-card:hover {
  background: rgba(20, 16, 40, 0.4);
  border-color: rgba(99, 102, 241, 0.35);
  box-shadow:
    0 0 24px rgba(99, 102, 241, 0.08),
    inset 0 0 24px rgba(99, 102, 241, 0.04);
}

.nav-card--pipeline {
  border-color: rgba(99, 102, 241, 0.15);
}

.nav-card--pipeline:hover {
  border-color: rgba(167, 139, 250, 0.4);
  box-shadow:
    0 0 32px rgba(99, 102, 241, 0.12),
    inset 0 0 32px rgba(99, 102, 241, 0.06);
}

.nav-card--meditation {
  border-color: rgba(217, 119, 6, 0.1);
}

.nav-card--meditation:hover {
  border-color: rgba(217, 119, 6, 0.3);
  box-shadow:
    0 0 24px rgba(217, 119, 6, 0.06),
    inset 0 0 24px rgba(217, 119, 6, 0.03);
}

.card-title {
  font-size: 1.05rem;
  font-weight: 600;
  letter-spacing: 0.01em;
}

.card-desc {
  font-size: 0.75rem;
  color: rgba(148, 163, 184, 0.7);
  line-height: 1.45;
  text-align: center;
}

.card-glare {
  position: absolute;
  inset: 0;
  pointer-events: none;
  border-radius: inherit;
  background: radial-gradient(
    circle at var(--gx, 50%) var(--gy, 50%),
    rgba(255, 255, 255, 0.08),
    transparent 60%
  );
  opacity: 0;
  transition: opacity 0.3s ease;
}

.nav-card:hover .card-glare { opacity: 1; }

@media (max-width: 480px) {
  .nav-grid { grid-template-columns: 1fr; }
  .nav-card { min-height: 100px; padding: 1.5rem 1.25rem; }
}
</style>
