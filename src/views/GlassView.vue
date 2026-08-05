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

      <!-- Text overlay — SHARED composer canvas (same drawFrame as export) -->
      <canvas
        ref="overlayRef"
        class="absolute inset-0 w-full h-full pointer-events-none"
      />

      <!-- Empty state -->
      <div v-if="!hasMedia" class="absolute inset-0 flex items-center justify-center">
        <div class="text-center space-y-4">
          <p class="text-slate-600 text-sm tracking-[0.2em] uppercase">Glass Studio</p>
          <p class="text-slate-700 text-xs max-w-xs mx-auto leading-relaxed">
            Upload a video or audio file, layer customizable subliminal text, add
            Tone.js synthesis that reacts to the speech, and export the composition.
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

    <!-- ── Editor panel (Text / Sound tabs) ── -->
    <Transition name="fade">
      <div
        v-if="activePanel"
        class="relative z-20 bg-black/70 backdrop-blur-xl border-t border-white/[0.04] px-4 py-3 max-h-[45vh] overflow-y-auto"
      >
        <TextControls v-if="activePanel === 'text'" :layers="composition.textLayers" />
        <SoundControls
          v-else-if="activePanel === 'sound'"
          :binaural="composition.binaural"
          :active-beat-hz="studioBinaural.activeBeatHz.value"
          :tone-presets="presetLabels"
          :active-tone-preset="activePreset"
          @apply="onBinauralApply"
          @volume="onBinauralVolume"
          @tone="(k: string) => selectPreset(k as TonePreset)"
        />
      </div>
    </Transition>

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

        <!-- Quick text (binds the first / title layer) -->
        <input
          v-model="quickText"
          placeholder="Overlay text..."
          class="bg-transparent border-b border-white/10 focus:border-white/30 text-white text-sm px-2 py-1 w-28 sm:w-40 outline-none placeholder-slate-600 transition-colors font-light tracking-wide"
        />

        <!-- Panel toggles -->
        <button
          @click="togglePanel('text')"
          class="px-2.5 py-1 rounded-full text-[10px] tracking-wider transition-all border whitespace-nowrap shrink-0"
          :class="activePanel === 'text'
            ? 'bg-white/10 border-white/20 text-white/90'
            : 'bg-transparent border-white/[0.06] text-white/40 hover:text-white/60 hover:border-white/10'"
        >
          Text ({{ composition.textLayers.length }})
        </button>
        <button
          @click="togglePanel('sound')"
          class="px-2.5 py-1 rounded-full text-[10px] tracking-wider transition-all border whitespace-nowrap shrink-0"
          :class="activePanel === 'sound'
            ? 'bg-white/10 border-white/20 text-white/90'
            : 'bg-transparent border-white/[0.06] text-white/40 hover:text-white/60 hover:border-white/10'"
        >
          Sound<span v-if="composition.binaural.enabled" class="text-emerald-400/80"> ♪</span>
        </button>

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
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import * as Tone from 'tone'
import { useAudioSync } from '@/composables/useAudioSync'
import { useGlassTones, PRESET_LABELS, type TonePreset } from '@/composables/useGlassTones'
import { useGlassExport } from '@/composables/useGlassExport'
import { useStudioBinaural } from '@/composables/useStudioBinaural'
import { drawFrame } from '@/composables/useGlassComposer'
import { makeDefaultComposition } from '@/composables/studioTypes'
import TextControls from '@/components/studio/TextControls.vue'
import SoundControls from '@/components/studio/SoundControls.vue'

// ── Refs ──
const mediaRef = ref<HTMLVideoElement | null>(null)
const vizRef = ref<HTMLCanvasElement | null>(null)
const overlayRef = ref<HTMLCanvasElement | null>(null)

const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const mediaType = ref<'video' | 'audio' | ''>('')
const mediaUrl = ref('')
const fileName = ref('')
const activePanel = ref<'text' | 'sound' | null>(null)
const hasMedia = computed(() => !!mediaUrl.value)

function togglePanel(p: 'text' | 'sound') {
  activePanel.value = activePanel.value === p ? null : p
}

// ── Composition (in-memory) ──
const composition = reactive(makeDefaultComposition())

// Quick text binds the first/title layer's primary line (preserves old behavior).
const quickText = computed({
  get: () => composition.textLayers[0]?.content[0] ?? '',
  set: (v: string) => {
    const l = composition.textLayers[0]
    if (l) l.content = [v, ...l.content.slice(1)]
  },
})

// ── Composables ──
const sync = useAudioSync()
const tones = useGlassTones()
const studioBinaural = useStudioBinaural(composition.binaural)
const { isRecording: isExporting, progress: exportProgress, startExport, stopExport: cancelExport } = useGlassExport()

const presetLabels = PRESET_LABELS
const activePreset = tones.activePreset

// Wire audio analysis → tone modulation + visualiser
sync.onFrame((env, speaking) => {
  tones.update(env, speaking)
  if (mediaType.value === 'audio' && vizRef.value) drawViz(env)
})

// ── Shared-composer overlay loop (matches export exactly) ──
let overlayRaf: number | undefined

function overlayLoop() {
  overlayRaf = requestAnimationFrame(overlayLoop)
  const canvas = overlayRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const dpr = window.devicePixelRatio || 1
  const w = canvas.clientWidth
  const h = canvas.clientHeight
  if (w === 0 || h === 0) return
  if (canvas.width !== Math.round(w * dpr) || canvas.height !== Math.round(h * dpr)) {
    canvas.width = Math.round(w * dpr)
    canvas.height = Math.round(h * dpr)
  }
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  ctx.clearRect(0, 0, w, h)

  // Export re-draws text on a canvas frame while recording; skip preview draw
  // then to avoid double compositing artifacts.
  if (isExporting.value || !mediaRef.value) return
  const clockMs = mediaRef.value.currentTime * 1000
  // Pass the live binaural beat so `syncToBeat` motion pulses in the preview.
  const beatHz = composition.binaural.enabled ? studioBinaural.activeBeatHz.value : undefined
  drawFrame(ctx, clockMs, composition.textLayers, { w, h }, beatHz)
}

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
  // Journey phases auto-fit to the media length.
  studioBinaural.setMediaDuration(mediaRef.value.duration)
  await Tone.start()
  await sync.connect(mediaRef.value)
}

function onTimeUpdate() {
  if (!mediaRef.value) return
  currentTime.value = mediaRef.value.currentTime
  // Advance the binaural journey off the media clock (no-op in preset mode).
  studioBinaural.tickJourney(mediaRef.value.currentTime)
}

function onEnded() {
  if (!isExporting.value) {
    isPlaying.value = false
    studioBinaural.stop()
  }
}

async function togglePlay() {
  if (!mediaRef.value) return
  await Tone.start()
  if (isPlaying.value) {
    mediaRef.value.pause()
    studioBinaural.stop()
  } else {
    await mediaRef.value.play()
    if (composition.binaural.enabled) await studioBinaural.start()
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

// ── Binaural (Sound panel) ──
// `apply` fires after a band/mode/journey/enable change → re-sync the engine.
async function onBinauralApply() {
  if (composition.binaural.enabled && isPlaying.value) {
    await studioBinaural.start() // idempotent init + applies current config
  } else if (!composition.binaural.enabled) {
    studioBinaural.stop()
  } else {
    // Enabled but paused — just keep config in sync for the next play.
    studioBinaural.refresh()
  }
}

function onBinauralVolume(v: number) {
  studioBinaural.setVolume(v)
}

// ── Export ──
async function doExport() {
  if (!mediaRef.value) return
  isPlaying.value = true

  // Start the beat first so its graph lives in Tone's shared context and its
  // output node can be routed into the export's MediaStreamAudioDestination
  // (same context = the beat actually lands in the file).
  const extraNodes: AudioNode[] = []
  let beatHz: number | undefined
  if (composition.binaural.enabled) {
    await studioBinaural.start()
    const node = studioBinaural.getOutputNode()
    if (node) extraNodes.push(node)
    beatHz = studioBinaural.activeBeatHz.value
  }

  await startExport(
    mediaRef.value,
    composition.textLayers,
    sync.getAnalyserNode(),
    tones.getMasterNode(),
    extraNodes,
    beatHz,
  )
}

// ── Lifecycle ──
onMounted(() => {
  overlayRaf = requestAnimationFrame(overlayLoop)
})

onUnmounted(() => {
  if (overlayRaf) cancelAnimationFrame(overlayRaf)
  sync.disconnect()
  tones.dispose()
  studioBinaural.destroy()
  if (mediaUrl.value) URL.revokeObjectURL(mediaUrl.value)
})
</script>

<style scoped>
.ctrl-btn {
  @apply w-9 h-9 rounded-full bg-white/5 hover:bg-white/10
         border border-white/[0.06] text-white/50 hover:text-white/80
         flex items-center justify-center transition-all shrink-0 active:scale-95;
}

.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
