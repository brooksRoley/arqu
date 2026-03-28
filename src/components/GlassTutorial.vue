<template>
  <Transition name="tutorial-fade">
    <div v-if="isActive" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <!-- Dim backdrop — click to skip -->
      <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="skip" />

      <!-- Step card -->
      <Transition name="card-slide" mode="out-in">
        <div :key="currentStep" class="relative z-10 max-w-sm w-full bg-slate-900/80 backdrop-blur-xl rounded-2xl border border-slate-700/40 shadow-2xl p-6 text-center">

          <!-- ── Welcome ── -->
          <template v-if="currentStep === 'welcome'">
            <div class="step-label">Glass Studio</div>
            <h2 class="step-title">Welcome</h2>
            <p class="step-body">
              Project text and media onto a liquid glass canvas.
              We'll walk through the tools quickly.
            </p>
            <button @click="advance" class="step-btn">Begin &rarr;</button>
          </template>

          <!-- ── Step 1: Oscillator ── -->
          <template v-if="currentStep === 'oscillator'">
            <div class="step-label">1 / 4</div>
            <h2 class="step-title">Basic Oscillator</h2>
            <p class="step-body">
              Hold the button to play a sine tone. This wakes up the browser audio context.
            </p>
            <button
              @mousedown="playSynth"
              @mouseup="stopSynth"
              @mouseleave="stopSynth"
              @touchstart.prevent="playSynth"
              @touchend.prevent="stopSynth"
              class="w-full px-6 py-3 bg-emerald-600/80 hover:bg-emerald-500 text-white rounded-full font-medium text-sm tracking-wider transition-all active:scale-95 mb-4"
            >
              Hold to Play C4
            </button>
            <Transition name="card-slide">
              <button v-if="oscPlayed" @click="advance" class="step-btn">Next &rarr;</button>
            </Transition>
          </template>

          <!-- ── Step 2: AutoFilter ── -->
          <template v-if="currentStep === 'filter'">
            <div class="step-label">2 / 4</div>
            <h2 class="step-title">AutoFilter Sweep</h2>
            <p class="step-body">
              Noise routed through an LFO-driven filter. The frequency sweeps on a quarter-note rhythm.
            </p>
            <button
              @click="toggleNoise"
              class="w-full px-6 py-3 text-white rounded-full font-medium text-sm tracking-wider transition-all active:scale-95 mb-4"
              :class="isNoisePlaying ? 'bg-rose-600/80 hover:bg-rose-500' : 'bg-purple-600/80 hover:bg-purple-500'"
            >
              {{ isNoisePlaying ? 'Stop Sweep' : 'Start Sweep' }}
            </button>
            <Transition name="card-slide">
              <button v-if="filterPlayed" @click="advance" class="step-btn">Next &rarr;</button>
            </Transition>
          </template>

          <!-- ── Step 3: Upload ── -->
          <template v-if="currentStep === 'upload'">
            <div class="step-label">3 / 4</div>
            <h2 class="step-title">Load Media</h2>
            <p class="step-body">
              Upload an MP3 or MP4 to loop on the canvas. Video plays behind the glass layer so you
              can see it through the liquid effect.
            </p>
            <button @click="advance" class="step-btn">Got it &rarr;</button>
          </template>

          <!-- ── Step 4: Mantra ── -->
          <template v-if="currentStep === 'mantra'">
            <div class="step-label">4 / 4</div>
            <h2 class="step-title">Project Text</h2>
            <p class="step-body">
              Type a mantra or affirmation in the toolbar. It renders full-viewport with blend-mode
              exclusion over the glass.
            </p>
            <button @click="advance" class="step-btn">Let's Go &rarr;</button>
          </template>

          <!-- Skip link -->
          <button @click="skip" class="mt-4 block mx-auto text-xs text-slate-600 hover:text-slate-400 transition-colors tracking-wider uppercase">
            Skip Tutorial
          </button>
        </div>
      </Transition>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref, onUnmounted } from 'vue'
import * as Tone from 'tone'
import { useGlassTutorial } from '@/composables/useGlassTutorial'

const { currentStep, isActive, advance, skip } = useGlassTutorial()

// ── Synth demo ──
let synth: Tone.Synth | null = null
const oscPlayed = ref(false)

const playSynth = async () => {
  await Tone.start()
  if (!synth) synth = new Tone.Synth().toDestination()
  synth.triggerAttack('C4')
  oscPlayed.value = true
}
const stopSynth = () => synth?.triggerRelease()

// ── Noise + AutoFilter demo ──
let noiseSynth: Tone.NoiseSynth | null = null
let autoFilter: Tone.AutoFilter | null = null
const isNoisePlaying = ref(false)
const filterPlayed = ref(false)

const toggleNoise = async () => {
  await Tone.start()
  if (!noiseSynth) {
    autoFilter = new Tone.AutoFilter('4n').toDestination().start()
    noiseSynth = new Tone.NoiseSynth().connect(autoFilter)
  }
  if (isNoisePlaying.value) {
    noiseSynth.triggerRelease()
  } else {
    noiseSynth.triggerAttack()
    filterPlayed.value = true
  }
  isNoisePlaying.value = !isNoisePlaying.value
}

onUnmounted(() => {
  synth?.dispose()
  noiseSynth?.dispose()
  autoFilter?.dispose()
})
</script>

<style scoped>
.step-label {
  @apply text-xs uppercase tracking-[0.25em] text-slate-500 mb-3;
}
.step-title {
  @apply text-xl font-light text-white tracking-wide mb-2;
}
.step-body {
  @apply text-sm text-slate-400 leading-relaxed mb-6;
}
.step-btn {
  @apply px-6 py-2.5 bg-white/10 hover:bg-white/20 text-white/80 rounded-full text-sm tracking-wider transition-all border border-white/10;
}

/* ── Transitions ── */
.tutorial-fade-enter-active,
.tutorial-fade-leave-active {
  transition: opacity 0.6s ease;
}
.tutorial-fade-enter-from,
.tutorial-fade-leave-to {
  opacity: 0;
}
.card-slide-enter-active,
.card-slide-leave-active {
  transition: all 0.35s ease;
}
.card-slide-enter-from {
  opacity: 0;
  transform: translateY(16px);
}
.card-slide-leave-to {
  opacity: 0;
  transform: translateY(-12px);
}
</style>
