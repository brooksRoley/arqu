<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'

interface Phase {
  name: string
  start: number
  end: number
  hz: number
  band: string
}

const TOTAL = 25
const PHASES: Phase[] = [
  { name: 'Settle',  start: 0,  end: 5,  hz: 10, band: 'Alpha' },
  { name: 'Descent', start: 5,  end: 10, hz: 8,  band: 'Alpha→Theta' },
  { name: 'Deepen',  start: 10, end: 17, hz: 6,  band: 'Theta' },
  { name: 'Rise',    start: 17, end: 22, hz: 8,  band: 'Theta→Alpha' },
  { name: 'Return',  start: 22, end: 25, hz: 10, band: 'Alpha' },
]

const cursor = ref(0)
let raf = 0
let t0 = 0
const LOOP_S = 12

function tick() {
  const dt = (performance.now() - t0) / 1000
  cursor.value = (dt % LOOP_S) / LOOP_S * TOTAL
  raf = requestAnimationFrame(tick)
}

onMounted(() => {
  t0 = performance.now()
  raf = requestAnimationFrame(tick)
})

onBeforeUnmount(() => cancelAnimationFrame(raf))

const cursorPct = computed(() => (cursor.value / TOTAL) * 100)
const activePhase = computed(() =>
  PHASES.find((p) => cursor.value >= p.start && cursor.value < p.end) ?? PHASES[PHASES.length - 1]
)

const minHz = 4
const maxHz = 14

function hzToY(hz: number): number {
  return 100 - ((hz - minHz) / (maxHz - minHz)) * 100
}

const linePoints = computed(() => {
  const W = 100
  const segs: string[] = []
  PHASES.forEach((p) => {
    const x1 = (p.start / TOTAL) * W
    const x2 = (p.end / TOTAL) * W
    const y = hzToY(p.hz)
    segs.push(`${x1},${y}`)
    segs.push(`${x2},${y}`)
  })
  return segs.join(' ')
})

const yAlpha = hzToY(10)
const yTheta = hzToY(6)
</script>

<template>
  <figure class="proto">
    <div class="chart-wrap">
      <svg viewBox="0 0 100 100" preserveAspectRatio="none" class="chart" aria-hidden="true">
        <line x1="0" :y1="yAlpha" x2="100" :y2="yAlpha" class="band-line" />
        <line x1="0" :y1="yTheta" x2="100" :y2="yTheta" class="band-line" />

        <g v-for="(p, i) in PHASES" :key="p.name">
          <rect
            :x="(p.start / TOTAL) * 100"
            y="0"
            :width="((p.end - p.start) / TOTAL) * 100"
            height="100"
            :class="['phase-bg', { 'phase-bg--active': activePhase.name === p.name }]"
          />
          <line
            v-if="i > 0"
            :x1="(p.start / TOTAL) * 100"
            y1="0"
            :x2="(p.start / TOTAL) * 100"
            y2="100"
            class="phase-divider"
          />
        </g>

        <polyline :points="linePoints" class="freq-line" />

        <line :x1="cursorPct" y1="0" :x2="cursorPct" y2="100" class="cursor" />
        <circle
          :cx="cursorPct"
          :cy="hzToY(activePhase.hz)"
          r="1.4"
          class="cursor-dot"
        />
      </svg>

      <div class="band-labels" aria-hidden="true">
        <span class="band-label" :style="{ top: `calc(${yAlpha}% - 8px)` }">α 10 Hz</span>
        <span class="band-label" :style="{ top: `calc(${yTheta}% - 8px)` }">θ 6 Hz</span>
      </div>

      <div class="phase-labels" aria-hidden="true">
        <span
          v-for="p in PHASES"
          :key="p.name"
          :class="['phase-label', { 'phase-label--active': activePhase.name === p.name }]"
          :style="{
            left: `${(p.start / TOTAL) * 100}%`,
            width: `${((p.end - p.start) / TOTAL) * 100}%`,
          }"
        >{{ p.name }}</span>
      </div>
    </div>

    <div class="readout">
      <div class="readout-row">
        <span class="readout-key">phase</span>
        <span class="readout-val">{{ activePhase.name }}</span>
      </div>
      <div class="readout-row">
        <span class="readout-key">band</span>
        <span class="readout-val">{{ activePhase.band }}</span>
      </div>
      <div class="readout-row">
        <span class="readout-key">beat</span>
        <span class="readout-val">{{ activePhase.hz }} Hz</span>
      </div>
      <div class="readout-row">
        <span class="readout-key">time</span>
        <span class="readout-val">{{ cursor.toFixed(1) }} / {{ TOTAL }} min</span>
      </div>
    </div>
  </figure>
</template>

<style scoped>
.proto {
  margin: 0 0 2.5rem;
}

.chart-wrap {
  position: relative;
  background: #141420;
  border: 1px solid #2a2a2a;
  border-radius: 10px;
  padding: 1.25rem 3.25rem 2rem 3.25rem;
}

.chart {
  display: block;
  width: 100%;
  height: 160px;
  overflow: visible;
}

.band-line {
  stroke: rgba(148, 163, 184, 0.18);
  stroke-width: 0.3;
  stroke-dasharray: 0.8 1.2;
  vector-effect: non-scaling-stroke;
}

.phase-bg {
  fill: transparent;
  transition: fill 220ms ease;
}

.phase-bg--active {
  fill: rgba(99, 102, 241, 0.07);
}

.phase-divider {
  stroke: rgba(255, 255, 255, 0.04);
  stroke-width: 0.3;
  vector-effect: non-scaling-stroke;
}

.freq-line {
  fill: none;
  stroke: #818cf8;
  stroke-width: 1.6;
  vector-effect: non-scaling-stroke;
  filter: drop-shadow(0 0 6px rgba(129, 140, 248, 0.35));
}

.cursor {
  stroke: #a5b4fc;
  stroke-width: 0.6;
  vector-effect: non-scaling-stroke;
  opacity: 0.6;
}

.cursor-dot {
  fill: #fff;
  filter: drop-shadow(0 0 4px rgba(165, 180, 252, 0.8));
}

.band-labels {
  position: absolute;
  left: 0.5rem;
  top: 1.25rem;
  bottom: 2rem;
  width: 2.6rem;
  font-size: 0.65rem;
  color: #64748b;
  font-variant-numeric: tabular-nums;
}

.band-label {
  position: absolute;
  font-size: 0.65rem;
  letter-spacing: 0.04em;
}

.phase-labels {
  position: absolute;
  left: 3.25rem;
  right: 3.25rem;
  bottom: 0.4rem;
  height: 1.25rem;
}

.phase-label {
  position: absolute;
  bottom: 0;
  text-align: center;
  font-size: 0.62rem;
  color: #475569;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  transition: color 180ms ease;
}

.phase-label--active {
  color: #a5b4fc;
}

.readout {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 0.5rem 1.25rem;
  margin-top: 0.875rem;
  padding: 0.75rem 1rem;
  background: #181828;
  border: 1px solid #2a2a2a;
  border-radius: 8px;
  font-size: 0.78rem;
}

.readout-row {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
}

.readout-key {
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 0.65rem;
}

.readout-val {
  color: #e2e8f0;
  font-variant-numeric: tabular-nums;
}

@media (prefers-reduced-motion: reduce) {
  .cursor, .cursor-dot {
    display: none;
  }
}
</style>
