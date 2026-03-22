import { ref, computed, readonly } from 'vue'

// ── Text-to-Speech composable ──────────────────────────────────────
// Phase 1: Web Speech API (free, built-in, zero dependencies)
// Phase 2: Swap in open source engine (Piper / Coqui) via same interface

export type TTSStatus = 'idle' | 'speaking' | 'paused'

// ── Module-level singleton state ───────────────────────────────────

const status = ref<TTSStatus>('idle')
const currentText = ref('')
const voiceIndex = ref(0)
const rate = ref(0.95)       // slightly slower for reflective content
const pitch = ref(1.0)
const volume = ref(1.0)
const availableVoices = ref<SpeechSynthesisVoice[]>([])
const progress = ref(0)      // 0–100 based on char boundary events
const supported = ref(typeof window !== 'undefined' && 'speechSynthesis' in window)

let utterance: SpeechSynthesisUtterance | null = null
let totalChars = 0

// ── Voice loading ──────────────────────────────────────────────────

function loadVoices() {
  if (!supported.value) return
  const voices = speechSynthesis.getVoices()
  if (voices.length > 0) {
    availableVoices.value = voices
    // Prefer a natural-sounding English voice
    const preferred = voices.findIndex(
      (v) => v.lang.startsWith('en') && (v.name.includes('Natural') || v.name.includes('Google'))
    )
    if (preferred >= 0) voiceIndex.value = preferred
  }
}

// Voices load asynchronously in most browsers
if (supported.value) {
  loadVoices()
  if (speechSynthesis.onvoiceschanged !== undefined) {
    speechSynthesis.onvoiceschanged = loadVoices
  }
}

// ── Derived ────────────────────────────────────────────────────────

const selectedVoice = computed(() => availableVoices.value[voiceIndex.value] ?? null)

const isSpeaking = computed(() => status.value === 'speaking')
const isPaused = computed(() => status.value === 'paused')
const isIdle = computed(() => status.value === 'idle')

// ── Actions ────────────────────────────────────────────────────────

function speak(text: string) {
  if (!supported.value || !text.trim()) return
  stop() // cancel anything in flight

  currentText.value = text
  totalChars = text.length
  progress.value = 0

  utterance = new SpeechSynthesisUtterance(text)
  if (selectedVoice.value) utterance.voice = selectedVoice.value
  utterance.rate = rate.value
  utterance.pitch = pitch.value
  utterance.volume = volume.value

  utterance.onboundary = (e: SpeechSynthesisEvent) => {
    if (totalChars > 0) {
      progress.value = Math.round((e.charIndex / totalChars) * 100)
    }
  }

  utterance.onend = () => {
    status.value = 'idle'
    progress.value = 100
    utterance = null
  }

  utterance.onerror = () => {
    status.value = 'idle'
    progress.value = 0
    utterance = null
  }

  speechSynthesis.speak(utterance)
  status.value = 'speaking'
}

function pause() {
  if (!supported.value || status.value !== 'speaking') return
  speechSynthesis.pause()
  status.value = 'paused'
}

function resume() {
  if (!supported.value || status.value !== 'paused') return
  speechSynthesis.resume()
  status.value = 'speaking'
}

function stop() {
  if (!supported.value) return
  speechSynthesis.cancel()
  status.value = 'idle'
  progress.value = 0
  utterance = null
}

function toggle(text?: string) {
  if (status.value === 'speaking') {
    pause()
  } else if (status.value === 'paused') {
    resume()
  } else if (text) {
    speak(text)
  }
}

function setVoice(index: number) {
  voiceIndex.value = index
}

function setRate(r: number) {
  rate.value = Math.max(0.25, Math.min(4, r))
}

function setPitch(p: number) {
  pitch.value = Math.max(0, Math.min(2, p))
}

function setVolume(v: number) {
  volume.value = Math.max(0, Math.min(1, v))
}

// ── Export ──────────────────────────────────────────────────────────

export function useTTS() {
  return {
    // State
    status: readonly(status),
    currentText: readonly(currentText),
    progress: readonly(progress),
    supported: readonly(supported),
    availableVoices: readonly(availableVoices),
    selectedVoice,
    isSpeaking,
    isPaused,
    isIdle,
    rate,
    pitch,
    volume,
    voiceIndex,

    // Actions
    speak,
    pause,
    resume,
    stop,
    toggle,
    setVoice,
    setRate,
    setPitch,
    setVolume,
  }
}
