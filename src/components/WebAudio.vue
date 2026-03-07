<template>
  <div class="trance-container" :style="{ opacity: avFlash ? 0.8 : 1 }">
    <canvas ref="canvasBus" class="spiral-canvas"></canvas>

    <div
      v-if="phase === 'coherence'"
      class="pacer-ring"
      :class="{ expanding: isExpanding }"
    ></div>

    <div class="ui-layer">
      <nav v-if="phase === 'coherence'" class="hud-top">
        <div class="stat">
          <label>COHERENCE</label>
          <span :class="{ linked: coherenceScore > 70 }">{{ coherenceScore }}%</span>
        </div>
        <div class="stat">
          <label>PHASE</label>
          <span>{{ phase.toUpperCase() }}</span>
        </div>
      </nav>

      <div v-if="phase !== 'idle' && phase !== 'coherence'" class="status-bar">
        <span class="phase-label">Phase: {{ phase }}</span>
        <div class="progress-track">
          <div class="fill" :style="{ width: progress + '%' }"></div>
        </div>
      </div>

      <div class="controls" v-if="!sessionActive">
        <h1>Binaural Induction Terminal</h1>
        <button @click="startSession" class="start-btn">BEGIN ENTRAINMENT</button>
      </div>

      <div class="interaction-zone" v-else>
        <transition name="fade" mode="out-in">
          <h2
            v-if="phase === 'coherence'"
            :key="currentInstruction"
            class="instruction-text"
          >
            {{ currentInstruction }}
          </h2>
          <p v-else class="instruction">{{ currentInstruction }}</p>
        </transition>

        <p v-if="phase === 'coherence'" class="sync-hint">Hold to match the pulse</p>

        <button
          @pointerdown="startSync"
          @pointerup="stopSync"
          class="sync-pad"
          :class="{ syncing: isSyncing }"
        >
          {{ phase === 'coherence' ? 'HOLD TO SYNC' : 'SYNC BREATH' }}
        </button>

        <button @click="stopSession" class="stop-btn">STOP SESSION</button>
      </div>
    </div>

    <!-- Tutorial overlay -->
    <div v-if="tutorialInfo" class="tutorial-card">
      <div class="tutorial-title">{{ tutorialInfo.title }}</div>
      <div class="tutorial-text">{{ tutorialInfo.text }}</div>
      <button class="tutorial-dismiss" @click="dismissTutorial">Dismiss Tutorial</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useTranceEngine } from '@/composables/useTranceEngine'

const {
  phase,
  sessionActive,
  coherenceScore,
  progress,
  isExpanding,
  currentInstruction,
  isSyncing,
  tunnelPulseStrength,
  avSyncActive,
  startSession,
  stopSession,
  startSync,
  stopSync,
  toggleAVSync,
} = useTranceEngine()

// --- Star Field (visual only) ---
const STAR_COUNT = 400
const stars = []

class Star {
  constructor(canvas) {
    this.reset(canvas)
  }
  reset(canvas) {
    this.x = (Math.random() - 0.5) * canvas.width * 2
    this.y = (Math.random() - 0.5) * canvas.height * 2
    this.z = canvas.width
    this.px = 0
    this.py = 0
  }
  update(speed, canvas) {
    this.px = this.x / (this.z / canvas.width)
    this.py = this.y / (this.z / canvas.width)
    this.z -= speed
    if (this.z < 1) this.reset(canvas)
  }
}

const canvasBus = ref(null)
const avFlash = ref(false)
let animFrameId

// --- AV Sync flash handler ---
function onAVFlash(flash) {
  avFlash.value = flash
}

// --- Tutorial ---
const tutorialActive = ref(!localStorage.getItem('trance-tutorial-done'))

const tutorialInfo = computed(() => {
  if (!tutorialActive.value) return null
  switch (phase.value) {
    case 'idle':
      return {
        title: 'Welcome',
        text: 'Use stereo headphones for the full binaural effect. Click BEGIN ENTRAINMENT to start your session.',
      }
    case 'induction':
      return {
        title: 'Induction Phase',
        text: 'Binaural tones are synchronizing. Breathe slowly and follow the rhythm. This phase lasts ~30 seconds.',
      }
    case 'coherence':
      return {
        title: 'Coherence Phase',
        text: 'The ring expands on inhale, contracts on exhale. Hold SYNC to match your breath. Aim for 70% coherence.',
      }
    case 'deepen':
      return {
        title: 'Deep Entrainment',
        text: 'You\'ve achieved coherence. Bass pulses drive deeper. Try additional modules from the navbar menu.',
      }
    default:
      return null
  }
})

function dismissTutorial() {
  tutorialActive.value = false
  localStorage.setItem('trance-tutorial-done', '1')
}

// --- Tunnel Rendering ---
const renderTunnel = () => {
  if (!canvasBus.value) return
  const ctx = canvasBus.value.getContext('2d')
  const { width, height } = canvasBus.value

  ctx.fillStyle = 'rgba(0, 0, 0, 0.15)'
  ctx.fillRect(0, 0, width, height)

  const currentSpeed = 5 + tunnelPulseStrength.value * 20
  tunnelPulseStrength.value *= 0.9

  ctx.strokeStyle = 'white'
  ctx.beginPath()
  stars.forEach((star) => {
    star.update(currentSpeed, canvasBus.value)
    const x2d = star.x / (star.z / width) + width / 2
    const y2d = star.y / (star.z / height) + height / 2
    if (star.px !== 0) {
      ctx.moveTo(star.px + width / 2, star.py + height / 2)
      ctx.lineTo(x2d, y2d)
    }
  })
  ctx.stroke()

  animFrameId = requestAnimationFrame(renderTunnel)
}

onMounted(() => {
  canvasBus.value.width = window.innerWidth
  canvasBus.value.height = window.innerHeight

  for (let i = 0; i < STAR_COUNT; i++) {
    stars.push(new Star(canvasBus.value))
  }

  renderTunnel()
})

onUnmounted(() => {
  if (animFrameId) cancelAnimationFrame(animFrameId)
})
</script>

<style scoped>
.trance-container {
  background: #050505;
  height: 100vh;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  transition: opacity 0.05s ease;
  position: relative;
}

.spiral-canvas {
  position: absolute;
  z-index: 1;
}

/* Pacer ring */
.pacer-ring {
  position: absolute;
  width: 320px;
  height: 320px;
  border-radius: 50%;
  border: 2px solid rgba(74, 144, 226, 0.5);
  box-shadow: 0 0 20px rgba(74, 144, 226, 0.2);
  transform: scale(0.75);
  transition:
    transform 5s linear,
    box-shadow 5s linear;
  z-index: 2;
  pointer-events: none;
}

.pacer-ring.expanding {
  transform: scale(1.35);
  box-shadow: 0 0 40px rgba(74, 144, 226, 0.5);
}

.ui-layer {
  position: relative;
  z-index: 3;
  text-align: center;
  background: rgba(0, 0, 0, 0.4);
  padding: 2rem;
  border-radius: 20px;
  backdrop-filter: blur(5px);
  min-width: 280px;
}

/* HUD */
.hud-top {
  display: flex;
  justify-content: space-around;
  margin-bottom: 1.5rem;
  gap: 2rem;
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
}

.stat label {
  font-size: 0.65rem;
  letter-spacing: 0.15em;
  color: #666;
}

.stat span {
  font-size: 1.2rem;
  font-weight: 600;
  color: #4a90e2;
  transition:
    color 0.5s,
    text-shadow 0.5s;
}

.stat span.linked {
  color: #7fff7f;
  text-shadow: 0 0 12px rgba(127, 255, 127, 0.6);
}

/* Instruction text with crossfade */
.instruction-text {
  font-size: 1.6rem;
  letter-spacing: 0.2em;
  margin: 1rem 0;
  color: rgba(255, 255, 255, 0.9);
  text-shadow: 0 0 20px rgba(74, 144, 226, 0.5);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.8s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.sync-hint {
  font-size: 0.8rem;
  color: #555;
  margin-bottom: 0.5rem;
  letter-spacing: 0.1em;
}

/* Status bar (pre-coherence) */
.status-bar {
  margin-bottom: 1rem;
}

.phase-label {
  font-size: 0.85rem;
  color: #888;
}

.progress-track {
  width: 200px;
  height: 4px;
  background: #333;
  margin: 10px auto;
}

.fill {
  height: 100%;
  background: #4a90e2;
  transition: width 0.5s;
}

.sync-pad {
  margin-top: 20px;
  padding: 20px 40px;
  border-radius: 50px;
  border: 2px solid #4a90e2;
  background: transparent;
  color: white;
  cursor: pointer;
  letter-spacing: 0.1em;
  transition: all 0.3s;
}

.sync-pad:active,
.sync-pad.syncing {
  background: rgba(74, 144, 226, 0.25);
  border-color: #7fb8ff;
  box-shadow: 0 0 20px rgba(74, 144, 226, 0.4);
}

.instruction {
  color: #aaa;
  margin-bottom: 1rem;
}

.stop-btn {
  display: block;
  margin: 1rem auto 0;
  padding: 0.4rem 1rem;
  border-radius: 6px;
  border: 1px solid rgba(255, 80, 80, 0.4);
  background: transparent;
  color: #ff6b6b;
  font-size: 0.7rem;
  letter-spacing: 0.1em;
  cursor: pointer;
  transition: all 0.2s;
}

.stop-btn:hover {
  background: rgba(255, 80, 80, 0.15);
  border-color: #ff6b6b;
}

/* Tutorial card */
.tutorial-card {
  position: absolute;
  bottom: 2rem;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10;
  background: rgba(10, 10, 30, 0.85);
  border: 1px solid rgba(74, 144, 226, 0.3);
  border-radius: 12px;
  padding: 1rem 1.5rem;
  max-width: 420px;
  width: 90%;
  backdrop-filter: blur(8px);
}

.tutorial-title {
  font-size: 0.75rem;
  letter-spacing: 0.15em;
  color: #4a90e2;
  text-transform: uppercase;
  margin-bottom: 0.5rem;
}

.tutorial-text {
  font-size: 0.85rem;
  color: #ccc;
  line-height: 1.5;
}

.tutorial-dismiss {
  margin-top: 0.75rem;
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: #888;
  padding: 0.25rem 0.75rem;
  border-radius: 4px;
  font-size: 0.7rem;
  cursor: pointer;
  letter-spacing: 0.05em;
  transition: all 0.2s;
}

.tutorial-dismiss:hover {
  color: #ccc;
  border-color: rgba(255, 255, 255, 0.3);
}
</style>
