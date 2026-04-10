<template>
  <div class="spotify-scene">

    <!-- Cosmic base layer -->
    <canvas ref="cosmicCanvas" class="scene-canvas" />

    <!-- Overlay: genre labels, valence field, hover state -->
    <canvas ref="overlayCanvas" class="scene-canvas scene-canvas--overlay" />

    <!-- Loading -->
    <div v-if="!loaded" class="scene-hud scene-hud--center">
      <p class="hud-mono">mapping your sonic field...</p>
    </div>

    <!-- No data -->
    <div v-if="loaded && !profile" class="scene-hud scene-hud--center">
      <p class="hud-mono">no spotify data yet —</p>
      <router-link to="/calibrate" class="hud-link">connect spotify on calibrate</router-link>
    </div>

    <!-- Audio stats HUD (bottom left) -->
    <div v-if="profile && audioSummary" class="scene-hud scene-hud--stats">
      <p class="hud-label">sonic field</p>
      <div class="stat-row" v-for="stat in statBars" :key="stat.key">
        <span class="stat-name">{{ stat.label }}</span>
        <div class="stat-track">
          <div class="stat-fill" :style="{ width: `${stat.value * 100}%`, background: stat.color }"></div>
        </div>
        <span class="stat-val">{{ stat.display }}</span>
      </div>
    </div>

    <!-- Genre + artist legend (top right, collapsed by default) -->
    <div v-if="profile" class="scene-hud scene-hud--legend" :class="{ expanded: legendOpen }">
      <button class="legend-toggle" @click="legendOpen = !legendOpen">
        {{ legendOpen ? '×' : '◎' }}
      </button>
      <template v-if="legendOpen">
        <p class="hud-label" style="margin-bottom:0.5rem">your field</p>
        <div v-for="(genre, i) in topGenres" :key="genre" class="legend-row">
          <span
            class="legend-dot"
            :style="{ background: `rgb(${orbDefs[i]?.r},${orbDefs[i]?.g},${orbDefs[i]?.b})` }"
          ></span>
          <span class="legend-genre">{{ genre }}</span>
        </div>
        <div class="legend-artists">
          <p class="hud-label" style="margin-top:0.75rem;margin-bottom:0.35rem">top artists</p>
          <span v-for="a in profile.top_artists" :key="a" class="artist-chip">{{ a }}</span>
        </div>
      </template>
    </div>

    <!-- Hover tooltip (genre orb title) -->
    <div v-if="hoveredIdx !== null && topGenres[hoveredIdx]" class="scene-hud scene-hud--hint">
      hover → {{ topGenres[hoveredIdx] }}
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '@/composables/useAuthStore'
import { useSpotifyPhysics, type SpotifyPhysicsProfile } from '@/composables/useSpotifyPhysics'

const { apiFetch } = useAuthStore()

const cosmicCanvas  = ref<HTMLCanvasElement>()
const overlayCanvas = ref<HTMLCanvasElement>()

const profile       = ref<SpotifyPhysicsProfile | null>(null)
const loaded        = ref(false)
const legendOpen    = ref(false)

// ── Lazy-init physics after profile loads ────────────────────────────────────
let physics: ReturnType<typeof useSpotifyPhysics> | null = null

const hoveredIdx   = computed(() => physics?.hoveredIdx.value ?? null)
const topGenres    = computed(() => physics?.topGenres ?? [])
const orbDefs      = computed(() => physics?.orbDefs ?? [])
const audioSummary = computed(() => physics?.audioSummary ?? null)

const statBars = computed(() => {
  const s = audioSummary.value
  if (!s) return []
  return [
    { key: 'valence',      label: 'valence',      value: s.valence,      display: s.valence.toFixed(2),      color: valenceColor(s.valence) },
    { key: 'energy',       label: 'energy',       value: s.energy,       display: s.energy.toFixed(2),       color: '#f97316' },
    { key: 'danceability', label: 'dance',         value: s.danceability, display: s.danceability.toFixed(2), color: '#a78bfa' },
    { key: 'acousticness', label: 'acoustic',      value: s.acousticness, display: s.acousticness.toFixed(2), color: '#34d399' },
    { key: 'tempo',        label: 'tempo',         value: Math.min(1, s.tempo / 200), display: `${s.tempo} bpm`, color: '#60a5fa' },
  ]
})

function valenceColor(v: number) {
  if (v > 0.65) return '#fbbf24'
  if (v < 0.35) return '#818cf8'
  return '#c084fc'
}

onMounted(async () => {
  try {
    const data = await apiFetch<SpotifyPhysicsProfile | null>('/api/spotify/profile')
    profile.value = data
  } catch { /* no data */ }

  if (profile.value) {
    physics = useSpotifyPhysics(cosmicCanvas, overlayCanvas, profile.value)
    await physics.init()
  }

  loaded.value = true
})

onUnmounted(() => {
  physics?.destroy()
})
</script>

<style scoped>
.spotify-scene {
  position: fixed;
  inset: 0;
  background: #08060e;
  overflow: hidden;
}

.scene-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.scene-canvas--overlay {
  pointer-events: none; /* mouse events handled by the composable directly */
  z-index: 1;
}
/* Re-enable pointer events on overlay so hover works */
.scene-canvas--overlay { pointer-events: auto; }

/* ── HUD shell ── */
.scene-hud {
  position: absolute;
  z-index: 10;
  color: #94a3b8;
  font-family: 'monospace', monospace;
}

.scene-hud--center {
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  pointer-events: none;
}

.scene-hud--stats {
  bottom: 2rem;
  left: 2rem;
  background: rgba(8, 6, 14, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 0.75rem;
  padding: 0.9rem 1.1rem;
  backdrop-filter: blur(12px);
  min-width: 200px;
}

.scene-hud--legend {
  top: 1.5rem;
  right: 1.5rem;
  background: rgba(8, 6, 14, 0.75);
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 0.75rem;
  padding: 0.75rem;
  backdrop-filter: blur(12px);
  max-width: 200px;
  transition: all 0.2s ease;
}

.scene-hud--hint {
  bottom: 2rem;
  left: 50%;
  transform: translateX(-50%);
  font-size: 0.65rem;
  color: #475569;
  pointer-events: none;
}

/* ── Stat bars ── */
.hud-label {
  font-size: 0.55rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: #334155;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.hud-mono {
  font-size: 0.8rem;
  color: #475569;
  font-family: monospace;
}

.hud-link {
  font-size: 0.75rem;
  color: #6366f1;
  text-decoration: none;
}

.stat-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.4rem;
}

.stat-name {
  font-size: 0.6rem;
  color: #64748b;
  width: 52px;
  flex-shrink: 0;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.stat-track {
  flex: 1;
  height: 3px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 2px;
  overflow: hidden;
}

.stat-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
  opacity: 0.85;
}

.stat-val {
  font-size: 0.6rem;
  color: #475569;
  width: 46px;
  text-align: right;
  flex-shrink: 0;
}

/* ── Legend ── */
.legend-toggle {
  display: block;
  background: none;
  border: none;
  color: #475569;
  font-size: 1rem;
  cursor: pointer;
  padding: 0;
  line-height: 1;
  transition: color 0.15s;
}
.legend-toggle:hover { color: #94a3b8; }

.legend-row {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  margin-bottom: 0.3rem;
}

.legend-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
  opacity: 0.8;
}

.legend-genre {
  font-size: 0.68rem;
  color: #94a3b8;
  text-transform: capitalize;
}

.legend-artists {
  border-top: 1px solid rgba(255,255,255,0.05);
  padding-top: 0.5rem;
}

.artist-chip {
  display: inline-block;
  font-size: 0.6rem;
  color: #64748b;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 100px;
  padding: 0.15rem 0.5rem;
  margin: 0.15rem 0.15rem 0 0;
}
</style>
