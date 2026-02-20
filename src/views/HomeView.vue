<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'

const navCards = [
  {
    icon: '📖',
    title: 'Text Stories',
    description: 'Speed-read through uploaded stories and text',
    to: '/reader'
  },
  {
    icon: '🌀',
    title: 'Zeromind',
    description: 'Generative visuals with streaming text',
    to: '/zeromind'
  },
  {
    icon: '🎵',
    title: 'Audio',
    description: 'Browse and play background audio tracks',
    to: '/audio'
  },
  {
    icon: '💧',
    title: 'Resume',
    description: 'Interactive liquid glass resume',
    to: '/resume'
  },
  {
    icon: '🌀',
    title: 'Spiral',
    description: 'Hypnotic spiral with trance words',
    to: '/spiral'
  },
  {
    icon: '🎧',
    title: 'Trance Tones',
    description: 'Trance tone engine experience',
    to: '/trance'
  }
]

// ── Scene drag tilt ──────────────────────────────────────────────
// Drag anywhere to tilt the whole scene in 3D (professional depth)
const sceneTilt = reactive({ x: 0, y: 0 })
let tiltTarget = { x: 0, y: 0 }
let isDragging = false
let lastDragX = 0
let lastDragY = 0
let springId: number | null = null

function runSpring() {
  tiltTarget.x *= 0.87
  tiltTarget.y *= 0.87
  sceneTilt.x += (tiltTarget.x - sceneTilt.x) * 0.11
  sceneTilt.y += (tiltTarget.y - sceneTilt.y) * 0.11
  if (Math.abs(sceneTilt.x) > 0.02 || Math.abs(sceneTilt.y) > 0.02) {
    springId = requestAnimationFrame(runSpring)
  } else {
    sceneTilt.x = 0
    sceneTilt.y = 0
    springId = null
  }
}

function startSpring() {
  if (springId) cancelAnimationFrame(springId)
  springId = requestAnimationFrame(runSpring)
}

function onMouseDown(e: MouseEvent) {
  isDragging = true
  lastDragX = e.clientX
  lastDragY = e.clientY
  if (springId) { cancelAnimationFrame(springId); springId = null }
}

function onMouseMove(e: MouseEvent) {
  if (!isDragging) return
  const dx = e.clientX - lastDragX
  const dy = e.clientY - lastDragY
  lastDragX = e.clientX
  lastDragY = e.clientY
  tiltTarget.y = Math.max(-9, Math.min(9, tiltTarget.y + dx * 0.06))
  tiltTarget.x = Math.max(-6, Math.min(6, tiltTarget.x - dy * 0.06))
  sceneTilt.x = tiltTarget.x
  sceneTilt.y = tiltTarget.y
}

function onMouseUp() {
  if (!isDragging) return
  isDragging = false
  startSpring()
}

function onTouchStart(e: TouchEvent) {
  const t = e.touches[0]
  lastDragX = t.clientX
  lastDragY = t.clientY
  if (springId) { cancelAnimationFrame(springId); springId = null }
}

function onTouchMove(e: TouchEvent) {
  const t = e.touches[0]
  const dx = t.clientX - lastDragX
  const dy = t.clientY - lastDragY
  lastDragX = t.clientX
  lastDragY = t.clientY
  tiltTarget.y = Math.max(-9, Math.min(9, tiltTarget.y + dx * 0.04))
  tiltTarget.x = Math.max(-6, Math.min(6, tiltTarget.x - dy * 0.04))
  sceneTilt.x = tiltTarget.x
  sceneTilt.y = tiltTarget.y
}

function onTouchEnd() {
  startSpring()
}

const sceneStyle = computed(() => ({
  transform: `perspective(1100px) rotateX(${sceneTilt.x}deg) rotateY(${sceneTilt.y}deg)`
}))

// Title shifts opposite to tilt — it reads as "further back" in the scene
const titleStyle = computed(() => ({
  transform: `translate(${-sceneTilt.y * 3.5}px, ${sceneTilt.x * 2.5}px)`
}))

const subtitleStyle = computed(() => ({
  transform: `translate(${-sceneTilt.y * 2}px, ${sceneTilt.x * 1.5}px)`
}))

// ── Per-card 3D tilt + moving glare ─────────────────────────────
// Each card tilts independently toward the pointer and shows a
// directional highlight — precise, professional, tactile
interface CardState {
  tx: number  // rotateX degrees
  ty: number  // rotateY degrees
  gx: number  // glare center x %
  gy: number  // glare center y %
  hover: boolean
}

const cards = ref<CardState[]>(
  navCards.map(() => ({ tx: 0, ty: 0, gx: 50, gy: 50, hover: false }))
)

function onCardMove(e: PointerEvent, i: number) {
  const el = e.currentTarget as HTMLElement
  const r = el.getBoundingClientRect()
  const nx = (e.clientX - r.left) / r.width * 2 - 1   // -1 → 1
  const ny = (e.clientY - r.top) / r.height * 2 - 1   // -1 → 1
  const c = cards.value[i]
  c.tx = ny * -5
  c.ty = nx * 5
  c.gx = (nx + 1) * 50
  c.gy = (ny + 1) * 50
}

function onCardEnter(i: number) { cards.value[i].hover = true }

function onCardLeave(i: number) {
  const c = cards.value[i]
  c.tx = 0; c.ty = 0; c.gx = 50; c.gy = 50; c.hover = false
}

function cardStyle(i: number) {
  const c = cards.value[i]
  return {
    transform: `perspective(600px) rotateX(${c.tx}deg) rotateY(${c.ty}deg)`,
    '--gx': `${c.gx}%`,
    '--gy': `${c.gy}%`,
    transition: c.hover
      ? 'box-shadow 0.2s ease'
      : 'transform 0.6s cubic-bezier(0.23, 1, 0.32, 1), box-shadow 0.2s ease'
  }
}

onMounted(() => {
  window.addEventListener('mousedown', onMouseDown)
  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup', onMouseUp)
  window.addEventListener('touchstart', onTouchStart, { passive: true })
  window.addEventListener('touchmove', onTouchMove, { passive: true })
  window.addEventListener('touchend', onTouchEnd, { passive: true })
})

onUnmounted(() => {
  if (springId) cancelAnimationFrame(springId)
  window.removeEventListener('mousedown', onMouseDown)
  window.removeEventListener('mousemove', onMouseMove)
  window.removeEventListener('mouseup', onMouseUp)
  window.removeEventListener('touchstart', onTouchStart)
  window.removeEventListener('touchmove', onTouchMove)
  window.removeEventListener('touchend', onTouchEnd)
})
</script>

<template>
  <div class="home" @dragstart.prevent>
    <div class="content-scene" :style="sceneStyle">
      <h1 class="title" :style="titleStyle">Channel Zero</h1>
      <p class="subtitle" :style="subtitleStyle">Choose your experience</p>

      <div class="nav-grid">
        <router-link
          v-for="(card, i) in navCards"
          :key="card.title"
          :to="card.to"
          class="nav-card"
          :style="cardStyle(i)"
          @pointermove="onCardMove($event, i)"
          @pointerenter="onCardEnter(i)"
          @pointerleave="onCardLeave(i)"
        >
          <span class="card-icon">{{ card.icon }}</span>
          <span class="card-title">{{ card.title }}</span>
          <span class="card-desc">{{ card.description }}</span>
          <!-- Directional glare highlight that follows the pointer -->
          <div class="card-glare"></div>
        </router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.home {
  text-align: center;
  user-select: none;
  -webkit-user-select: none;
}

.content-scene {
  will-change: transform;
  transform-origin: center center;
}

.title {
  font-size: 2rem;
  font-weight: bold;
  margin-bottom: 0.5rem;
  color: #e2e8f0;
  margin-top: 2rem;
  will-change: transform;
}

.subtitle {
  font-size: 1rem;
  color: #94a3b8;
  margin-bottom: 2rem;
  will-change: transform;
}

.nav-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.25rem;
  max-width: 600px;
  margin: 0 auto;
}

.nav-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 2rem 1.5rem;
  background: rgba(30, 30, 50, 0.8);
  border: 1px solid rgba(100, 100, 255, 0.15);
  border-radius: 1rem;
  text-decoration: none;
  color: #e2e8f0;
  position: relative;
  overflow: hidden;
  will-change: transform;
  cursor: pointer;
}

.nav-card:hover {
  background: rgba(40, 40, 70, 0.9);
  border-color: rgba(99, 102, 241, 0.5);
  box-shadow: 0 12px 36px rgba(0, 0, 0, 0.45);
}

.card-icon {
  font-size: 2.5rem;
}

.card-title {
  font-size: 1.1rem;
  font-weight: 600;
}

.card-desc {
  font-size: 0.8rem;
  color: #94a3b8;
  line-height: 1.4;
}

/* Moving directional glare inside each card */
.card-glare {
  position: absolute;
  inset: 0;
  pointer-events: none;
  border-radius: inherit;
  background: radial-gradient(
    circle at var(--gx, 50%) var(--gy, 50%),
    rgba(255, 255, 255, 0.13),
    transparent 62%
  );
  opacity: 0;
  transition: opacity 0.3s ease;
}

.nav-card:hover .card-glare {
  opacity: 1;
}

@media (max-width: 480px) {
  .nav-grid {
    grid-template-columns: 1fr;
  }
}
</style>
