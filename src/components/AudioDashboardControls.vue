<template>
  <div
    class="fixed bottom-0 left-0 right-0 z-50 p-4 border-t bg-slate-900 border-slate-700/50 backdrop-blur-md"
  >
    <div class="max-w-4xl mx-auto flex items-center justify-between gap-6">
      <button
        @click="store.togglePlay"
        class="flex items-center justify-center w-12 h-12 transition-all rounded-full bg-emerald-500 hover:bg-emerald-400 text-slate-900 shadow-[0_0_15px_rgba(16,185,129,0.4)]"
      >
        <svg v-if="!store.isPlaying" class="w-6 h-6 ml-1" fill="currentColor" viewBox="0 0 24 24">
          <path d="M8 5v14l11-7z" />
        </svg>
        <svg v-else class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
          <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z" />
        </svg>
      </button>

      <div class="flex-1 flex items-center gap-4 text-xs font-mono text-slate-400">
        <span>{{ formatTime(store.currentTime) }}</span>

        <div class="relative flex-1 h-2 rounded-full bg-slate-800 overflow-hidden">
          <div
            class="absolute top-0 left-0 h-full bg-emerald-500 transition-all duration-75 ease-linear"
            :style="{ width: `${(store.currentTime / store.duration) * 100}%` }"
          ></div>
        </div>

        <span>{{ formatTime(store.duration) }}</span>
      </div>

      <div class="flex items-center gap-2 w-32">
        <svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5 10v4a2 2 0 002 2h2l5 5V3l-5 5H7a2 2 0 00-2 2z"
          ></path>
        </svg>
        <input
          type="range"
          min="0"
          max="1"
          step="0.01"
          v-model="store.volume"
          class="w-full accent-emerald-500"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useSyncStore } from '@/stores/useSyncStore'
import { useAudioEngine } from '@/composables/useAudioEngine'

const route = useRoute()
const store = useSyncStore()

let audioFile = '/audio/floating.mp3'
if (route.query.heavy !== undefined) {
  audioFile = '/audio/heavyGB.mp3'
} else if (route.query.gradual !== undefined) {
  audioFile = '/audio/gradualGB.mp3'
}

const { initAudio } = useAudioEngine(audioFile)

onMounted(() => {
  // Wait for user interaction to initialize AudioContext (browser policy)
  window.addEventListener('click', initAudio, { once: true })
})

const formatTime = (timeInSeconds) => {
  if (!timeInSeconds) return '0:00'
  const m = Math.floor(timeInSeconds / 60)
  const s = Math.floor(timeInSeconds % 60)
    .toString()
    .padStart(2, '0')
  return `${m}:${s}`
}
</script>
