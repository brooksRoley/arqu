<template>
  <div class="fixed bottom-0 inset-x-0 z-40">
    <div class="flex items-end justify-center p-4 gap-2">

      <!-- Expand / collapse -->
      <button @click="expanded = !expanded" class="tb-btn shrink-0" :title="expanded ? 'Collapse' : 'Expand'">
        <svg class="w-4 h-4 transition-transform duration-200" :class="{ 'rotate-180': expanded }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4.5 15.75l7.5-7.5 7.5 7.5" />
        </svg>
      </button>

      <Transition name="bar-slide">
        <div v-if="expanded" class="flex items-center gap-3 bg-black/40 backdrop-blur-xl rounded-2xl border border-white/[0.06] px-4 py-2.5">

          <!-- Upload -->
          <label class="tb-btn cursor-pointer relative" title="Upload media">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
            </svg>
            <input type="file" @change="$emit('upload', $event)" accept=".mp3,audio/*,video/mp4,.mp4" class="absolute inset-0 w-full h-full opacity-0 cursor-pointer" />
          </label>

          <!-- Filename indicator -->
          <span v-if="fileName" class="text-[10px] text-slate-500 tracking-wider max-w-[80px] truncate select-none">
            {{ fileName }}
          </span>

          <!-- Divider -->
          <div class="w-px h-5 bg-white/[0.06]" />

          <!-- Text input -->
          <input
            :value="modelValue"
            @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
            placeholder="Mantra..."
            class="bg-transparent border-b border-white/10 focus:border-white/30 text-white text-sm px-2 py-1 w-36 sm:w-48 outline-none placeholder-slate-600 transition-colors font-light tracking-wide"
          />

          <!-- Divider -->
          <div class="w-px h-5 bg-white/[0.06]" />

          <!-- Play / Pause -->
          <button @click="$emit('togglePlay')" :disabled="!canPlay" class="tb-btn disabled:opacity-20 disabled:cursor-default" title="Play / pause">
            <svg v-if="!isPlaying" class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
            <svg v-else class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
          </button>

          <!-- Save -->
          <button @click="$emit('save')" class="tb-btn" title="Save experiment JSON">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
            </svg>
          </button>
        </div>
      </Transition>

      <!-- Re-show tutorial -->
      <button v-if="showTutorialReset" @click="$emit('resetTutorial')" class="tb-btn shrink-0 text-[10px] font-bold" title="Show tutorial">
        ?
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

defineProps<{
  modelValue: string
  isPlaying: boolean
  canPlay: boolean
  fileName: string
  showTutorialReset: boolean
}>()

defineEmits<{
  'update:modelValue': [value: string]
  upload: [event: Event]
  togglePlay: []
  save: []
  resetTutorial: []
}>()

const expanded = ref(true)
</script>

<style scoped>
.tb-btn {
  @apply w-9 h-9 rounded-full bg-white/5 hover:bg-white/10
         border border-white/[0.06] text-white/50 hover:text-white/80
         flex items-center justify-center transition-all;
}

.bar-slide-enter-active,
.bar-slide-leave-active {
  transition: all 0.3s ease;
}
.bar-slide-enter-from,
.bar-slide-leave-to {
  opacity: 0;
  transform: translateY(8px) scale(0.97);
}
</style>
