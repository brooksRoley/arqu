<template>
  <div class="p-6 bg-slate-900/90 backdrop-blur-xl rounded-2xl border border-slate-700/50 shadow-2xl text-slate-300 w-full">
    <div class="mb-6 border-b border-slate-700 pb-4">
      <h2 class="text-2xl font-black text-white uppercase tracking-tight">Looper Studio</h2>
      <p class="text-sm mt-1 text-slate-400">Load a custom media file and project text onto the glass canvas.</p>
    </div>
    
    <!-- Media Upload -->
    <div class="mb-6">
      <label class="block text-xs font-bold uppercase tracking-wider mb-2 text-slate-400">1. Upload Track (MP3 / MP4)</label>
      <input type="file" @change="handleUpload" accept=".mp3,audio/*,video/mp4" class="block w-full text-sm text-slate-400 file:mr-4 file:py-2.5 file:px-5 file:rounded-lg file:border-0 file:text-xs file:font-bold file:uppercase file:tracking-wider file:bg-blue-600/20 file:text-blue-400 hover:file:bg-blue-600/30 file:transition-colors file:cursor-pointer p-1 bg-slate-800 rounded-xl" />
    </div>

    <!-- Text Overlay Input -->
    <div class="mb-6">
      <label class="block text-xs font-bold uppercase tracking-wider mb-2 text-slate-400">2. Projected Mantra (Text)</label>
      <textarea v-model="overlayText" rows="2" class="w-full bg-slate-800 border-x-0 border-t-0 border-b-2 border-b-slate-600 focus:border-b-blue-500 focus:ring-0 p-3 text-white placeholder-slate-500 font-mono text-lg transition-colors resize-none overflow-hidden" placeholder="Type words here..."></textarea>
    </div>

    <!-- Playback Controls -->
    <div class="flex gap-4 mb-8">
      <button @click="togglePlay" :disabled="!isReady" class="flex-1 py-3 px-6 rounded-xl font-black text-sm uppercase tracking-widest transition-all shadow-lg active:scale-95 disabled:opacity-30 disabled:pointer-events-none" :class="isPlaying ? 'bg-amber-500 hover:bg-amber-400 text-slate-950' : 'bg-blue-600 hover:bg-blue-500 text-white'">
        {{ isPlaying ? 'Pause Looper' : 'Play Looper' }}
      </button>
    </div>

    <!-- Save configuration -->
    <button @click="saveExperiment" class="w-full py-3 px-6 bg-slate-800 hover:bg-slate-700 text-white border border-slate-600 rounded-xl font-bold text-xs uppercase tracking-widest transition-colors flex items-center justify-center gap-2">
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4"></path></svg>
      Save Experiment (JSON)
    </button>

    <!-- The Text overlay and Background Media rendered via Teleport so their z-index isn't trapped -->
    <Teleport to="body">
       <!-- Background Video (if MP4) -->
       <div v-if="mediaType === 'video' && isPlaying" class="fixed inset-0 z-0 pointer-events-none">
          <video :src="mediaUrl" autoplay loop muted playsinline class="w-full h-full object-cover mix-blend-screen opacity-40"></video>
       </div>

       <!-- The immersive Text (Mix-blend mode allows it to interact with liquid glass) -->
       <div v-if="overlayText" class="fixed inset-0 pointer-events-none z-40 flex items-center justify-center p-4 sm:p-12 overflow-hidden mix-blend-exclusion">
          <h1 class="text-6vw sm:text-[12vw] leading-none font-black text-white text-center tracking-tighter uppercase break-words drop-shadow-2xl">
            {{ overlayText }}
          </h1>
       </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onUnmounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import * as Tone from 'tone'

const route = useRoute()

const mediaUrl = ref(route.query.heavy !== undefined ? '/hideBG.webm' : '')
const mediaType = ref(route.query.heavy !== undefined ? 'video' : '')
const overlayText = ref('')
const isPlaying = ref(false)
const originalFileName = ref('')

let player = null

const isReady = computed(() => !!mediaUrl.value)

const handleUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  originalFileName.value = file.name

  if (player) {
    player.stop()
    player.dispose()
    player = null
  }
  
  if (mediaUrl.value) URL.revokeObjectURL(mediaUrl.value)
  
  mediaUrl.value = URL.createObjectURL(file)
  mediaType.value = file.type.startsWith('video') ? 'video' : 'audio'
  isPlaying.value = false

  if (mediaType.value === 'audio') {
    // Tone Player setup
    await Tone.start()
    player = new Tone.Player({
      url: mediaUrl.value,
      loop: true,
      autostart: false
    }).toDestination()
  }
}

const togglePlay = async () => {
  await Tone.start()
  isPlaying.value = !isPlaying.value
  
  if (mediaType.value === 'audio' && player) {
    if (isPlaying.value) {
      if (player.loaded) {
         player.start()
      } else {
         player.autostart = true;
      }
    } else {
      player.stop()
    }
  }
}

const saveExperiment = () => {
  const data = JSON.stringify({
    text: overlayText.value,
    fileName: originalFileName.value || null,
    type: mediaType.value,
    timestamp: new Date().toISOString()
  }, null, 2)
  
  const blob = new Blob([data], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'glass-experiment.json'
  a.click()
  URL.revokeObjectURL(url)
}

onUnmounted(() => {
  if (player) {
    player.stop()
    player.dispose()
  }
  if (mediaUrl.value) URL.revokeObjectURL(mediaUrl.value)
})
</script>
