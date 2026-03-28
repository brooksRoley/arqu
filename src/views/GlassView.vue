<template>
  <div class="relative w-full h-screen bg-[#0a0a0a] overflow-hidden flex flex-col">

    <!-- ── Main viewport ── -->
    <div class="flex-1 relative overflow-hidden min-h-0">

      <!-- Video / audio element (hidden for audio-only, shown for video) -->
      <video
        ref="mediaRef"
        class="absolute inset-0 w-full h-full object-contain bg-black"
        :class="{ 'invisible': mediaType === 'audio' }"
        playsinline
        :loop="!isExporting"
        @loadedmetadata="onMediaLoaded"
        @timeupdate="onTimeUpdate"
        @ended="onEnded"
      />

      <!-- Audio-only waveform visualiser -->
      <canvas
        v-if="mediaType === 'audio' && hasMedia"
        ref="vizRef"
        class="absolute inset-0 w-full h-full"
      />

      <!-- Text overlay -->
      <div
        v-if="overlayText"
        class="absolute inset-0 flex items-center justify-center p-6 sm:p-12 pointer-events-none mix-blend-exclusion"
      >
        <h1 class="text-[6vw] sm:text-[10vw] leading-[0.95] font-black text-white text-center tracking-tighter uppercase break-words">
          {{ overlayText }}
        </h1>
      </div>

      <!-- Empty state -->
      <div v-if="!hasMedia" class="absolute inset-0 flex items-center justify-center">
        <div class="text-center space-y-4">
          <p class="text-slate-600 text-sm tracking-[0.2em] uppercase">Glass Studio</p>
          <p class="text-slate-700 text-xs max-w-xs mx-auto leading-relaxed">
            Upload a video or audio file, overlay text, layer Tone.js synthesis that
            reacts to the speech, and export the composition.
          </p>
          <label class="inline-block px-6 py-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-full text-white/60 hover:text-white/80 text-sm tracking-wider cursor-pointer transition-all">
            Upload Video or Audio
            <input type="file" @change="handleUpload" accept="video/*,audio/*" class="hidden" />
          </label>
        </div>
      </div>

      <!-- Export progress -->
      <Transition name="fade">
        <div v-if="isExporting" class="absolute inset-0 flex items-center justify-center bg-black/50 z-30">
          <div class="text-center">
            <p class="text-white/80 text-sm tracking-[0.2em] uppercase mb-3">Exporting&hellip;</p>
            <div class="w-48 h-1 bg-white/10 rounded-full overflow-hidden mx-auto">
              <div class="h-full bg-emerald-500 transition-all duration-150" :style="{ width: `${exportProgress * 100}%` }" />
            </div>
            <button @click="cancelExport" class="mt-4 text-xs text-white/30 hover:text-white/60 uppercase tracking-wider transition-colors">
              Cancel
            </button>
          </div>
        </div>
      </Transition>
    </div>

    <!-- ── Bottom controls ── -->
    <div class="relative z-20 bg-black/60 backdrop-blur-xl border-t border-white/[0.04] px-4 py-3 space-y-2.5">

      <!-- Transport -->
      <div class="flex items-center gap-3">
        <button @click="togglePlay" :disabled="!hasMedia" class="ctrl-btn disabled:opacity-20">
          <svg v-if="!isPlaying" class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
          <svg v-else class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
        </button>

        <span class="text-[10px] text-slate-500 font-mono w-10 text-right shrink-0">{{ fmt(currentTime) }}</span>
        <input
          type="range" min="0" :max="duration" :value="currentTime" @input="seek" step="0.1"
          class="flex-1 h-1 accent-white/40 cursor-pointer" :disabled="!hasMedia"
        />
        <span class="text-[10px] text-slate-500 font-mono w-10 shrink-0">{{ fmt(duration) }}</span>
      </div>

      <!-- Tools -->
      <div class="flex items-center gap-3 flex-wrap">
        <!-- Upload -->
        <label class="ctrl-btn cursor-pointer relative shrink-0" title="Upload media">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
          </svg>
          <input type="file" @change="handleUpload" accept="video/*,audio/*" class="absolute inset-0 w-full h-full opacity-0 cursor-pointer" />
        </label>
        <span v-if="fileName" class="text-[10px] text-slate-600 truncate max-w-[100px] shrink-0">{{ fileName }}</span>

        <div class="w-px h-5 bg-white/[0.06] shrink-0" />

        <!-- Text input -->
        <input
          v-model="overlayText"
          placeholder="Overlay text..."
          class="bg-transparent border-b border-white/10 focus:border-white/30 text-white text-sm px-2 py-1 w-36 sm:w-48 outline-none placeholder-slate-600 transition-colors font-light tracking-wide"
        />

        <div class="w-px h-5 bg-white/[0.06] shrink-0" />

        <!-- Tone presets -->
        <div class="flex gap-1.5 flex-wrap">
          <button
            v-for="(label, key) in presetLabels"
            :key="key"
            @click="selectPreset(key as TonePreset)"
            class="px-2.5 py-1 rounded-full text-[10px] tracking-wider transition-all border whitespace-nowrap"
            :class="activePreset === key
              ? 'bg-white/10 border-white/20 text-white/90'
              : 'bg-transparent border-white/[0.06] text-white/30 hover:text-white/50 hover:border-white/10'"
          >
            {{ label }}
          </button>
        </div>

        <div class="flex-1 min-w-0" />

        <!-- Export -->
        <button
          @click="doExport"
          :disabled="!hasMedia || isExporting"
          class="px-4 py-1.5 bg-emerald-600/20 hover:bg-emerald-600/30 border border-emerald-500/30 text-emerald-400/80 hover:text-emerald-400 rounded-full text-[11px] tracking-wider transition-all disabled:opacity-20 disabled:cursor-default shrink-0"
        >
          Export
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue'
import * as Tone from 'tone'
import { useAudioSync } from '@/composables/useAudioSync'
import { useGlassTones, PRESET_LABELS, type TonePreset } from '@/composables/useGlassTones'
import { useGlassExport } from '@/composables/useGlassExport'

// ── Refs ──
const mediaRef = ref<HTMLVideoElement | null>(null)
const vizRef = ref<HTMLCanvasElement | null>(null)

const overlayText = ref('')
const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const mediaType = ref<'video' | 'audio' | ''>('')
const mediaUrl = ref('')
const fileName = ref('')
const hasMedia = computed(() => !!mediaUrl.value)

// ── Composables ──
const sync = useAudioSync()
const tones = useGlassTones()
const { isRecording: isExporting, progress: exportProgress, startExport, stopExport: cancelExport } = useGlassExport()

const presetLabels = PRESET_LABELS
const activePreset = tones.activePreset

// Wire audio analysis → tone modulation + visualiser
sync.onFrame((env, speaking) => {
  tones.update(env, speaking)
  if (mediaType.value === 'audio' && vizRef.value) drawViz(env)
})

// ── Audio-only waveform ring ──
function drawViz(env: number) {
  const canvas = vizRef.value!
  const ctx = canvas.getContext('2d')!
  const dpr = window.devicePixelRatio || 1
  const w = canvas.clientWidth
  const h = canvas.clientHeight
  if (canvas.width !== w * dpr) {
    canvas.width = w * dpr
    canvas.height = h * dpr
    ctx.scale(dpr, dpr)
  }
  ctx.fillStyle = 'rgba(10,10,10,0.12)'
  ctx.fillRect(0, 0, w, h)

  const cx = w / 2, cy = h / 2
  const r = Math.min(w, h) * 0.18

  ctx.beginPath()
  ctx.arc(cx, cy, r + env * 50, 0, Math.PI * 2)
  ctx.strokeStyle = `rgba(100,180,255,${0.08 + env * 0.35})`
  ctx.lineWidth = 1.5
  ctx.stroke()

  const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, r)
  grad.addColorStop(0, `rgba(100,180,255,${env * 0.06})`)
  grad.addColorStop(1, 'transparent')
  ctx.fillStyle = grad
  ctx.fillRect(0, 0, w, h)
}

// ── Media handling ──
async function handleUpload(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file || !mediaRef.value) return

  fileName.value = file.name
  mediaType.value = file.type.startsWith('video') ? 'video' : 'audio'

  if (mediaUrl.value) URL.revokeObjectURL(mediaUrl.value)
  mediaUrl.value = URL.createObjectURL(file)
  mediaRef.value.src = mediaUrl.value
  isPlaying.value = false
  currentTime.value = 0
}

async function onMediaLoaded() {
  if (!mediaRef.value) return
  duration.value = mediaRef.value.duration
  await Tone.start()
  await sync.connect(mediaRef.value)
}

function onTimeUpdate() {
  if (mediaRef.value) currentTime.value = mediaRef.value.currentTime
}

function onEnded() {
  if (!isExporting.value) isPlaying.value = false
}

async function togglePlay() {
  if (!mediaRef.value) return
  await Tone.start()
  if (isPlaying.value) {
    mediaRef.value.pause()
  } else {
    await mediaRef.value.play()
  }
  isPlaying.value = !isPlaying.value
}

function seek(e: Event) {
  if (!mediaRef.value) return
  const t = parseFloat((e.target as HTMLInputElement).value)
  mediaRef.value.currentTime = t
  currentTime.value = t
}

function fmt(s: number): string {
  if (!isFinite(s)) return '0:00'
  return `${Math.floor(s / 60)}:${Math.floor(s % 60).toString().padStart(2, '0')}`
}

// ── Tone preset ──
async function selectPreset(preset: TonePreset) {
  await Tone.start()
  tones.setPreset(preset)
}

// ── Export ──
async function doExport() {
  if (!mediaRef.value) return
  isPlaying.value = true
  await startExport(
    mediaRef.value,
    overlayText.value,
    sync.getAnalyserNode(),
    tones.getMasterNode(),
  )
}

// ── Cleanup ──
onUnmounted(() => {
  sync.disconnect()
  tones.dispose()
  if (mediaUrl.value) URL.revokeObjectURL(mediaUrl.value)
})
</script>

<style scoped>
.ctrl-btn {
  @apply w-9 h-9 rounded-full bg-white/5 hover:bg-white/10
         border border-white/[0.06] text-white/50 hover:text-white/80
         flex items-center justify-center transition-all shrink-0;
}

.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
