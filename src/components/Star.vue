<script setup lang="ts">
// Star tunnel — hyperspace starfield with an optional Tone.js sub-bass pulse
// that lunges the tunnel forward on each drop.
//
// Tone is imported from npm (`tone` is in package.json) — previously this file
// was an unstructured snippet that assumed a `Tone` CDN global which was never
// loaded, so it could not run. Audio is created lazily inside a user-gesture
// handler because browsers (and Tone.start()) require one.
import { ref, onMounted, onUnmounted } from 'vue'
import * as Tone from 'tone'

const canvasRef = ref<HTMLCanvasElement | null>(null)
const tunnelPulseStrength = ref(0)
const audioRunning = ref(false)

const STAR_COUNT = 400
let animId: number | null = null
let loop: Tone.Loop | null = null
let subBass: Tone.MonoSynth | null = null

class Star {
  x = 0
  y = 0
  z = 0
  px = 0 // previous projected position, for the streak effect
  py = 0

  constructor(canvas: HTMLCanvasElement) {
    this.reset(canvas)
  }

  reset(canvas: HTMLCanvasElement) {
    this.x = (Math.random() - 0.5) * canvas.width * 2
    this.y = (Math.random() - 0.5) * canvas.height * 2
    this.z = canvas.width // start far away
    this.px = 0
    this.py = 0
  }

  update(speed: number, canvas: HTMLCanvasElement) {
    this.px = this.x / (this.z / canvas.width)
    this.py = this.y / (this.z / canvas.width)
    this.z -= speed // move toward camera
    if (this.z < 1) this.reset(canvas)
  }
}

const stars: Star[] = []

// ── Audio: deep sub-bass drop every half note, synced to a visual lunge ──
async function startAudio() {
  if (audioRunning.value) return
  try {
    await Tone.start() // must run inside a user gesture
    subBass = new Tone.MonoSynth({
      oscillator: { type: 'sine' },
      envelope: { attack: 0.02, decay: 0.4, sustain: 0.1, release: 0.8 },
    }).toDestination()

    loop = new Tone.Loop((time) => {
      // 1. Audio: trigger a deep sub-bass drop
      subBass?.triggerAttackRelease('E1', '8n', time)
      // 2. Visuals: deferred callback — runs on the requestAnimationFrame
      //    closest to `time`
      Tone.getDraw().schedule(() => {
        tunnelPulseStrength.value = 1.0 // visual flash / lunge
      }, time)
    }, '2n').start(0)

    Tone.getTransport().start()
    audioRunning.value = true
  } catch {
    // Audio is an enhancement — the starfield keeps rendering without it.
  }
}

// ── Render loop ──────────────────────────────────────────────────────────
function renderTunnel() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  const { width, height } = canvas

  // Fade previous frame slightly for "motion blur"
  ctx.fillStyle = 'rgba(0, 0, 0, 0.15)'
  ctx.fillRect(0, 0, width, height)

  // Speed increases when the audio pulse happens, then decays
  const currentSpeed = 5 + tunnelPulseStrength.value * 20
  tunnelPulseStrength.value *= 0.9

  ctx.strokeStyle = 'white'
  ctx.beginPath()
  for (const star of stars) {
    star.update(currentSpeed, canvas)
    // Project 3D coordinates to 2D
    const x2d = star.x / (star.z / width) + width / 2
    const y2d = star.y / (star.z / height) + height / 2
    if (star.px !== 0) {
      ctx.moveTo(star.px + width / 2, star.py + height / 2)
      ctx.lineTo(x2d, y2d)
    }
  }
  ctx.stroke()
  animId = requestAnimationFrame(renderTunnel)
}

onMounted(() => {
  const canvas = canvasRef.value
  if (!canvas) return
  canvas.width = canvas.clientWidth
  canvas.height = canvas.clientHeight
  stars.length = 0
  for (let i = 0; i < STAR_COUNT; i++) stars.push(new Star(canvas))
  renderTunnel()
})

onUnmounted(() => {
  if (animId !== null) cancelAnimationFrame(animId)
  loop?.dispose()
  subBass?.dispose()
  if (audioRunning.value) Tone.getTransport().stop()
})
</script>

<template>
  <div class="star-tunnel">
    <canvas ref="canvasRef" class="star-tunnel-canvas" @click="startAudio"></canvas>
    <p v-if="!audioRunning" class="star-tunnel-hint">Tap to enable sound</p>
  </div>
</template>

<style scoped>
.star-tunnel {
  position: relative;
  width: 100%;
  height: 100%;
  background: #000;
}

.star-tunnel-canvas {
  width: 100%;
  height: 100%;
  display: block;
}

.star-tunnel-hint {
  position: absolute;
  bottom: 1rem;
  left: 50%;
  transform: translateX(-50%);
  font-size: 0.75rem;
  color: #64748b;
  margin: 0;
  pointer-events: none;
}
</style>
