<template>
  <div class="p-6 bg-slate-900/90 backdrop-blur-xl rounded-2xl border border-slate-700/50 shadow-2xl text-slate-300 w-full transition-all">
    <div class="mb-6 border-b border-slate-700 pb-4">
      <h2 class="text-2xl font-black text-white uppercase tracking-tight">Tone.js Tutorial</h2>
      <p class="text-sm mt-1 text-slate-400">Step-by-step interactive examples of web synthesis. Start clicking around to authorize the AudioContext.</p>
    </div>
    
    <div class="space-y-4">
      
      <!-- Step 1 -->
      <div class="bg-slate-800/80 p-5 rounded-xl border-l-4 border-emerald-500 shadow-inner">
        <label class="flex items-start gap-4 cursor-pointer group">
          <div class="mt-1">
            <input type="checkbox" v-model="step1Done" class="form-checkbox w-5 h-5 rounded border-slate-600 text-emerald-500 focus:ring-0 bg-slate-900 transition-colors" />
          </div>
          <div class="flex-1">
            <h3 class="font-bold text-white text-lg group-hover:text-emerald-400 transition-colors">1. Basic Oscillator</h3>
            <p class="text-xs mb-4 text-slate-400 leading-relaxed">Connect a simple synth directly to the destination and play a basic C4 note.</p>
            <button @mousedown="playSynth" @mouseup="stopSynth" @mouseleave="stopSynth" @touchstart.prevent="playSynth" @touchend.prevent="stopSynth" class="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-bold text-xs uppercase tracking-wider transition-all shadow-lg active:scale-95 active:shadow-none w-full sm:w-auto">
              Hold to Play C4
            </button>
          </div>
        </label>
      </div>

      <!-- Step 2 -->
      <div class="bg-slate-800/80 p-5 rounded-xl border-l-4 border-purple-500 shadow-inner transition-all duration-300" :class="{'opacity-50 grayscale pointer-events-none': !step1Done}">
        <label class="flex items-start gap-4 cursor-pointer group">
           <div class="mt-1">
            <input type="checkbox" v-model="step2Done" class="form-checkbox w-5 h-5 rounded border-slate-600 text-purple-500 focus:ring-0 bg-slate-900 transition-colors" />
          </div>
          <div class="flex-1">
            <h3 class="font-bold text-white text-lg group-hover:text-purple-400 transition-colors">2. AutoFilter Effect</h3>
            <p class="text-xs mb-4 text-slate-400 leading-relaxed">Route a continuous NoiseSynth through an AutoFilter (LFO-driven filter sweep) before hitting the destination.</p>
            <button @click="toggleNoise" class="px-5 py-2.5 hover:bg-purple-500 text-white rounded-lg font-bold text-xs uppercase tracking-wider transition-all shadow-lg active:scale-95 active:shadow-none w-full sm:w-auto" :class="isNoisePlaying ? 'bg-rose-600' : 'bg-purple-600'">
              {{ isNoisePlaying ? 'Stop Noise Sweep' : 'Start Noise Sweep' }}
            </button>
          </div>
        </label>
      </div>
      
      <div v-if="step2Done" class="mt-8 text-center animate-pulse text-sm text-emerald-400 font-bold uppercase tracking-[0.2em]">
        Move to the Looper Studio &rarr;
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onUnmounted } from 'vue'
import * as Tone from 'tone'

const step1Done = ref(false)
const step2Done = ref(false)

// Synth
let synth = null
const playSynth = async () => {
  await Tone.start()
  if (!synth) synth = new Tone.Synth().toDestination()
  synth.triggerAttack("C4")
}
const stopSynth = () => {
  if (synth) synth.triggerRelease()
}

// Noise + AutoFilter
let noiseSynth = null
let autoFilter = null
const isNoisePlaying = ref(false)

const toggleNoise = async () => {
  await Tone.start()
  if (!noiseSynth) {
    autoFilter = new Tone.AutoFilter("4n").toDestination().start()
    noiseSynth = new Tone.NoiseSynth().connect(autoFilter)
  }
  
  if (isNoisePlaying.value) {
    noiseSynth.triggerRelease()
  } else {
    noiseSynth.triggerAttack()
  }
  isNoisePlaying.value = !isNoisePlaying.value
}

onUnmounted(() => {
  if (synth) synth.dispose()
  if (noiseSynth) noiseSynth.dispose()
  if (autoFilter) autoFilter.dispose()
})
</script>
