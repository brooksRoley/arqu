<template>
  <div class="absolute inset-0 z-10 flex flex-col items-center justify-center font-mono">

    <div class="absolute top-8 left-8 z-20 space-y-2 pointer-events-none">
      <h2 class="text-purple-500 font-bold tracking-widest uppercase text-sm">Vibe Transmission</h2>
      <p class="text-gray-500 text-xs">Capacity: 1 / 1 available this week.</p>
      <div class="flex items-center gap-2 mt-4">
        <div class="w-2 h-2 rounded-full bg-red-500" :class="{ 'animate-pulse': isRecording }"></div>
        <span class="text-red-500 text-xs font-bold">{{ isRecording ? 'CAPTURING CHAOS...' : 'STANDBY' }}</span>
      </div>
    </div>

    <canvas
      ref="glassCanvas"
      @pointerdown="startBuzzing"
      @pointermove="drawVibe"
      @pointerup="stopBuzzing"
      @pointerleave="stopBuzzing"
      class="absolute inset-0 w-full h-full cursor-crosshair touch-none mix-blend-screen"
    ></canvas>

    <div v-if="hasRecording && !isRecording" class="absolute bottom-12 z-20 flex gap-6 slide-up">
      <button @click="resetGlass" class="text-gray-400 hover:text-white px-4 py-2 text-sm tracking-wide transition-colors">
        SHATTER (DISCARD)
      </button>
      <button @click="transmitVibe" class="bg-purple-600 hover:bg-purple-500 text-white px-8 py-3 rounded-full font-bold shadow-[0_0_20px_rgba(147,51,234,0.6)] transition-all">
        TRANSMIT FREQUENCY
      </button>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import * as Tone from 'tone'

const glassCanvas = ref<HTMLCanvasElement | null>(null)
let ctx: CanvasRenderingContext2D | null = null

const isRecording = ref(false)
const hasRecording = ref(false)

// Tone.js audio nodes
let leftOsc: Tone.Oscillator | null = null
let rightOsc: Tone.Oscillator | null = null
let audioFilter: Tone.Filter | null = null
let pannerLeft: Tone.Panner | null = null
let pannerRight: Tone.Panner | null = null
const baseFreq = 200

// Interaction state
let lastX = 0
let lastY = 0

interface VibeNode {
  x: number
  y: number
  s: number
  t: number
}
let timeData: VibeNode[] = []

function resizeCanvas() {
  if (!glassCanvas.value) return
  glassCanvas.value.width = window.innerWidth
  glassCanvas.value.height = window.innerHeight
}

onMounted(() => {
  if (!glassCanvas.value) return
  ctx = glassCanvas.value.getContext('2d', { alpha: true })
  resizeCanvas()
  window.addEventListener('resize', resizeCanvas)

  // Clear to transparent so mix-blend-screen shows the layer beneath
  if (ctx) {
    ctx.clearRect(0, 0, glassCanvas.value.width, glassCanvas.value.height)
  }

  // Initialize binaural engine — two oscillators panned hard L/R
  pannerLeft = new Tone.Panner(-1).toDestination()
  pannerRight = new Tone.Panner(1).toDestination()

  leftOsc = new Tone.Oscillator(baseFreq, 'sine')
  rightOsc = new Tone.Oscillator(baseFreq + 4, 'sine') // 4Hz delta = theta waves

  leftOsc.connect(pannerLeft)
  rightOsc.connect(pannerRight)

  audioFilter = new Tone.Filter(1000, 'lowpass').toDestination()
  leftOsc.connect(audioFilter)
  rightOsc.connect(audioFilter)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeCanvas)
  leftOsc?.dispose()
  rightOsc?.dispose()
  audioFilter?.dispose()
  pannerLeft?.dispose()
  pannerRight?.dispose()
})

async function startBuzzing(e: PointerEvent) {
  if (hasRecording.value || !leftOsc || !rightOsc) return

  await Tone.start()
  isRecording.value = true
  lastX = e.clientX
  lastY = e.clientY

  leftOsc.start()
  rightOsc.start()

  timeData = []
}

function drawVibe(e: PointerEvent) {
  if (!isRecording.value || !ctx || !glassCanvas.value || !leftOsc || !rightOsc || !audioFilter) return

  const currentX = e.clientX
  const currentY = e.clientY

  const deltaX = currentX - lastX
  const deltaY = currentY - lastY
  const speed = Math.sqrt(deltaX * deltaX + deltaY * deltaY)

  // Map physical chaos to audio synthesis
  const dynamicFreq = baseFreq + (currentY / window.innerHeight) * 300
  leftOsc.frequency.rampTo(dynamicFreq, 0.1)
  rightOsc.frequency.rampTo(dynamicFreq + speed * 0.5, 0.1)

  // Horizontal movement opens the filter cutoff
  audioFilter.frequency.rampTo(100 + (currentX / window.innerWidth) * 4000, 0.1)

  // Visual render — liquid glass strokes
  ctx.beginPath()
  ctx.moveTo(lastX, lastY)
  ctx.lineTo(currentX, currentY)

  const hue = 260 + speed * 2 // purples bleeding into hot pinks
  ctx.strokeStyle = `hsla(${hue}, 100%, 60%, 0.8)`
  ctx.lineWidth = Math.max(2, 15 - speed * 0.2)
  ctx.lineCap = 'round'
  ctx.stroke()

  // Subtle fade for liquid-disappearing aesthetic
  ctx.fillStyle = 'rgba(0, 0, 0, 0.05)'
  ctx.fillRect(0, 0, glassCanvas.value.width, glassCanvas.value.height)

  // Store the vector data for transmission
  timeData.push({ x: currentX, y: currentY, s: speed, t: Date.now() })

  lastX = currentX
  lastY = currentY
}

function stopBuzzing() {
  if (!isRecording.value) return
  isRecording.value = false
  hasRecording.value = true

  leftOsc?.stop()
  rightOsc?.stop()
}

function resetGlass() {
  if (!ctx || !glassCanvas.value) return
  ctx.clearRect(0, 0, glassCanvas.value.width, glassCanvas.value.height)
  hasRecording.value = false
  timeData = []
}

function transmitVibe() {
  // Stringify timeData, encrypt, push to Neon DB.
  // Recipient's app replays the touch chaos through their own Tone.js oscillators.
  console.log('Transmitting raw emotional vector array:', timeData.length, 'nodes')

  resetGlass()
  // Route back to feed, lock feature for 7 days.
}
</script>

<style scoped>
.slide-up {
  animation: slideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(40px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
