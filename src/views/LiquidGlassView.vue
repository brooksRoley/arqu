<template>
  <div class="relative w-full h-screen bg-black overflow-hidden">
    <!-- Layer 0: Uploaded Background Media -->
    <div v-if="mediaUrl" class="absolute inset-0 w-full h-full z-0">
      <video v-if="mediaType === 'video'" :src="mediaUrl" class="w-full h-full object-cover" autoplay loop muted playsinline></video>
      <img v-else :src="mediaUrl" class="w-full h-full object-cover" />
    </div>

    <!-- Layer 1: Liquid Glass iframe (slightly opaque to reveal media) -->
    <iframe src="/liquid-glass.html" class="full-frame opacity-80" />

    <!-- Layer 2: Sine wave opacity throb linked to audio time -->
    <div
      class="bg-black absolute inset-0 pointer-events-none mix-blend-overlay z-20"
      :style="{
        // This creates a perfect 0.5Hz sine wave opacity throb linked to the exact audio time!
        opacity: 0.5 + Math.sin(syncStore.currentTime * Math.PI * 2 * 0.5) * 0.5
      }"
    ></div>

    <!-- Layer 3: Fullscreen Hypnotic Pattern when active -->
    <HypnoticPattern class="z-30" />

    <!-- Layer 4: Upload Button -->
    <div class="absolute top-4 right-4 z-40">
      <label class="cursor-pointer flex items-center gap-2 px-4 py-2 bg-slate-900/60 hover:bg-slate-800 border border-slate-700/50 backdrop-blur-md rounded-full text-slate-300 text-sm font-medium transition-all shadow-lg">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path></svg>
        <span>Set Background</span>
        <input type="file" class="hidden" @change="handleFileUpload" accept="image/*,video/*" />
      </label>
    </div>

    <!-- Layer 5: Audio Controls Fixed to Bottom -->
    <AudioDashboardControls class="z-50" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { useSyncStore } from '@/stores/useSyncStore'
import { useHypnosisStore } from '@/stores/useHypnosisStore'
import AudioDashboardControls from '@/components/AudioDashboardControls.vue'
import HypnoticPattern from '@/components/HypnoticPattern.vue'

const syncStore = useSyncStore()
const hypnosisStore = useHypnosisStore()
const route = useRoute()

const mediaUrl = ref(route.query.heavy !== undefined ? '/hideBG.webm' : '')
const mediaType = ref(route.query.heavy !== undefined ? 'video' : '')

const handleFileUpload = (event) => {
  const file = event.target.files[0]
  if (!file) return

  if (mediaUrl.value) URL.revokeObjectURL(mediaUrl.value)
  mediaUrl.value = URL.createObjectURL(file)
  mediaType.value = file.type.startsWith('video/') ? 'video' : 'image'
}
</script>

<style scoped>
.full-frame {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border: none;
  z-index: 10;
}
</style>
