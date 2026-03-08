import { ref, computed, readonly } from 'vue'
import * as Tone from 'tone'

export type TrancePhase = 'idle' | 'induction' | 'coherence' | 'deepen' | 'joy' | 'wake'

// ── Singleton reactive state ──
const phase = ref<TrancePhase>('idle')
const sessionActive = ref(false)
const coherenceScore = ref(0)
const progress = ref(0)
const syncCount = ref(0)
const isExpanding = ref(false)
const currentInstruction = ref('')
const isSyncing = ref(false)
const tunnelPulseStrength = ref(0)

// Feature module states
const baselineModulatorActive = ref(false)
const ptosisInducerActive = ref(false)
const avSyncActive = ref(false)

const BREATH_CYCLE = 10
const INHALE_TIME = 5

// ── Audio node refs (not reactive, module-level singletons) ──
let audioReady = false
let osc: Tone.Oscillator | null = null
let lfo: Tone.LFO | null = null
let gainNode: Tone.Gain | null = null
let subBass: Tone.Synth | null = null
let deepenLoop: Tone.Loop | null = null
let swellOsc: Tone.Oscillator | null = null
let swellGain: Tone.Gain | null = null
let coherenceLoopId: number | undefined
let syncStartTime = 0
let phaseTimer: ReturnType<typeof setTimeout> | null = null
let phraseTimers: ReturnType<typeof setTimeout>[] = []

// ── Guided phrase sequences ──────────────────────────────────────
const INDUCTION_PHRASES = [
  'Find a comfortable position...',
  'Close your eyes...',
  'Take a deep breath in...',
  'And slowly release...',
  'Feel the weight of your body...',
  'Sinking... with each breath...',
  'The sound carries you...',
  'You are safe here...',
  'Nothing to do...',
  'Just this moment...',
]

const DEEPEN_PHRASES = [
  'Deeper now...',
  'Further in...',
  'Let it take you...',
  'Surrender to the rhythm...',
  'Falling... softly...',
  'The pulse is yours...',
  'Nothing left to hold...',
  'Just the frequency...',
]

const JOY_PHRASES = [
  'A warmth begins...',
  'Spreading outward...',
  'A quiet joy...',
  'Let it fill you...',
  'You carry this with you...',
  'It is always here...',
]

const WAKE_PHRASES = [
  'Ten... feel this stillness...',
  'Eight... awareness returning...',
  'Six... breath deepening...',
  'Four... body beginning to stir...',
  'Two... gently returning...',
  'One... open your eyes...',
]

function clearPhraseTimers() {
  phraseTimers.forEach(clearTimeout)
  phraseTimers = []
}

function schedulePhrases(phrases: string[], intervalMs: number, onComplete?: () => void) {
  clearPhraseTimers()
  phraseTimers = phrases.map((text, i) =>
    setTimeout(() => {
      currentInstruction.value = text
      if (i === phrases.length - 1) onComplete?.()
    }, i * intervalMs)
  )
}

// Module 1: 2.4 Hz Baseline Modulator
let bmCarrier: Tone.Oscillator | null = null
let bmPulse: Tone.LFO | null = null

// Module 2: 0.5 Hz Ptosis Inducer
let piFilter: Tone.Filter | null = null
let piNoise: Tone.Noise | null = null
let piLFO: Tone.LFO | null = null

// Module 3: Synchronized AV Entrainment
let avSynth: Tone.Synth | null = null
let avVisualCallback: ((flash: boolean) => void) | null = null
let avLoopId: number | undefined

// ── Core audio setup ──
function initCoreAudio() {
  if (audioReady) return
  osc = new Tone.Oscillator(200, 'sine').start()
  gainNode = new Tone.Gain(0).toDestination()
  lfo = new Tone.LFO(12, 190, 210).connect(osc.frequency).start()
  osc.connect(gainNode)

  subBass = new Tone.Synth({
    oscillator: { type: 'sine' },
    envelope: { attack: 0.01, decay: 0.3, sustain: 0, release: 0.5 }
  }).toDestination()
  subBass.volume.value = -6
  audioReady = true
}

// ── Module 1: 2.4 Hz Baseline Modulator ──
// Carrier at 432 Hz with amplitude modulated at 2.4 Hz (square wave)
// to excite nervous system resonance
async function startBaselineModulator() {
  await Tone.start()
  if (bmCarrier) return
  bmCarrier = new Tone.Oscillator(432, 'sine').toDestination()
  bmCarrier.volume.value = -12
  bmPulse = new Tone.LFO({ frequency: 2.4, type: 'square', min: -24, max: 0 }).start()
  bmPulse.connect(bmCarrier.volume)
  bmCarrier.start()
  baselineModulatorActive.value = true
}

function stopBaselineModulator() {
  if (!bmCarrier) return
  bmCarrier.stop()
  bmCarrier.dispose()
  bmPulse?.dispose()
  bmCarrier = null
  bmPulse = null
  baselineModulatorActive.value = false
}

// ── Module 2: 0.5 Hz Drifting Ptosis Inducer ──
// Pink noise through a lowpass filter whose cutoff is modulated at 0.5 Hz,
// drifting down to 0.42 Hz over 5 minutes to compensate for neural adaptation
async function startPtosisInducer() {
  await Tone.start()
  if (piNoise) return
  piFilter = new Tone.Filter(300, 'lowpass').toDestination()
  piNoise = new Tone.Noise('pink').connect(piFilter)
  piNoise.volume.value = -12
  piLFO = new Tone.LFO({ frequency: 0.5, type: 'sine', min: 100, max: 800 }).start()
  piLFO.connect(piFilter.frequency)
  piNoise.start()
  piLFO.frequency.rampTo(0.42, 300)
  ptosisInducerActive.value = true
}

function stopPtosisInducer() {
  if (!piNoise) return
  piNoise.stop()
  piNoise.dispose()
  piLFO?.dispose()
  piFilter?.dispose()
  piNoise = null
  piLFO = null
  piFilter = null
  ptosisInducerActive.value = false
}

// ── Module 3: Synchronized Audiovisual Entrainment ──
// Transport at 144 BPM = 2.4 beats/second. A low synth pulse fires on every
// quarter note; an optional visual callback flashes the UI in sync.
async function startAVSync(onFlash?: (flash: boolean) => void) {
  await Tone.start()
  if (avSynth) return
  avVisualCallback = onFlash || null
  avSynth = new Tone.Synth().toDestination()
  avSynth.volume.value = -18

  Tone.getTransport().bpm.value = 144
  avLoopId = Tone.getTransport().scheduleRepeat((time) => {
    avSynth!.triggerAttackRelease('C2', '16n', time)
    Tone.getDraw().schedule(() => {
      avVisualCallback?.(true)
      setTimeout(() => avVisualCallback?.(false), 50)
    }, time)
  }, '4n') as unknown as number

  if (Tone.getTransport().state !== 'started') {
    Tone.getTransport().start()
  }
  avSyncActive.value = true
}

function stopAVSync() {
  if (!avSynth) return
  if (avLoopId !== undefined) Tone.getTransport().clear(avLoopId)
  avSynth.dispose()
  avSynth = null
  avVisualCallback = null
  avLoopId = undefined
  avSyncActive.value = false
}

// ── Phase helpers ──
function setupCoherenceLoop() {
  swellGain = new Tone.Gain(0).toDestination()
  swellOsc = new Tone.Oscillator(40, 'sine').connect(swellGain).start()

  coherenceLoopId = Tone.getTransport().scheduleRepeat((time) => {
    swellGain!.gain.rampTo(0.4, INHALE_TIME, time)

    Tone.getDraw().schedule(() => {
      currentInstruction.value = 'BREATHE IN'
      isExpanding.value = true
    }, time)

    Tone.getDraw().schedule(() => {
      currentInstruction.value = 'BREATHE OUT'
      isExpanding.value = false
    }, time + INHALE_TIME)

    swellGain!.gain.rampTo(0, INHALE_TIME, time + INHALE_TIME)
  }, BREATH_CYCLE) as unknown as number

  Tone.getTransport().start()
}

function scheduleDeepenSequence() {
  Tone.getTransport().start()
  deepenLoop = new Tone.Loop((time) => {
    subBass!.triggerAttackRelease('E1', '8n', time)
    Tone.getDraw().schedule(() => {
      tunnelPulseStrength.value = 1.0
    }, time)
  }, '2n').start(0)
}

function runInduction() {
  phase.value = 'induction'
  gainNode!.gain.rampTo(0.5, 5)
  lfo!.frequency.rampTo(6, 30)
  // Cycle through induction phrases every ~3s over the 30s window
  schedulePhrases(INDUCTION_PHRASES, 3000)
  phaseTimer = setTimeout(() => runCoherence(), 30000)
}

function runCoherence() {
  phase.value = 'coherence'
  clearPhraseTimers()
  setupCoherenceLoop()
}

function runDeepen() {
  if (phase.value === 'deepen') return
  phase.value = 'deepen'
  lfo!.frequency.rampTo(4.5, 60)
  if (swellOsc) { swellOsc.stop(); swellOsc.dispose(); swellOsc = null }
  if (swellGain) { swellGain.dispose(); swellGain = null }
  if (coherenceLoopId !== undefined) {
    Tone.getTransport().clear(coherenceLoopId)
    coherenceLoopId = undefined
  }
  scheduleDeepenSequence()
  // Cycle deepen phrases every ~8s
  schedulePhrases(DEEPEN_PHRASES, 8000)
}

function runJoy() {
  if (phase.value === 'joy') return
  phase.value = 'joy'
  // Audio: stop sub-bass pulses, soften gain
  if (deepenLoop) { deepenLoop.stop().dispose(); deepenLoop = null }
  gainNode?.gain.rampTo(0.2, 8)
  lfo?.frequency.rampTo(3, 12)
  // Joy phrases every ~4s, then auto-wake
  schedulePhrases(JOY_PHRASES, 4000, () => runWake())
}

function runWake() {
  phase.value = 'wake'
  // Audio: fade everything out over ~18s
  gainNode?.gain.rampTo(0, 18)
  lfo?.frequency.rampTo(1, 18)
  // Wake countdown phrases every ~3s, then end session
  schedulePhrases(WAKE_PHRASES, 3000, () => {
    setTimeout(() => stopSession(), 2000)
  })
}

// ── Public API ──
async function startSession() {
  await Tone.start()
  initCoreAudio()
  sessionActive.value = true
  syncCount.value = 0
  coherenceScore.value = 0
  progress.value = 0
  runInduction()
}

function windDown() {
  if (phase.value === 'deepen') runJoy()
  else if (phase.value === 'joy') runWake()
}

function stopSession() {
  clearPhraseTimers()
  if (phaseTimer) { clearTimeout(phaseTimer); phaseTimer = null }
  if (deepenLoop) { deepenLoop.stop().dispose(); deepenLoop = null }
  if (coherenceLoopId !== undefined) { Tone.getTransport().clear(coherenceLoopId); coherenceLoopId = undefined }
  if (swellOsc) { swellOsc.stop(); swellOsc.dispose(); swellOsc = null }
  if (swellGain) { swellGain.dispose(); swellGain = null }
  if (osc) { osc.stop(); osc.dispose(); osc = null }
  if (lfo) { lfo.dispose(); lfo = null }
  if (gainNode) { gainNode.dispose(); gainNode = null }
  if (subBass) { subBass.dispose(); subBass = null }
  stopBaselineModulator()
  stopPtosisInducer()
  stopAVSync()
  Tone.getTransport().stop()

  phase.value = 'idle'
  sessionActive.value = false
  coherenceScore.value = 0
  progress.value = 0
  syncCount.value = 0
  isExpanding.value = false
  currentInstruction.value = ''
  isSyncing.value = false
  audioReady = false
}

function startSync() {
  if (phase.value === 'coherence') {
    isSyncing.value = true
    syncStartTime = Tone.getTransport().seconds
    tunnelPulseStrength.value = 0.2
  } else {
    syncCount.value++
    progress.value = Math.min(progress.value + 5, 100)
    tunnelPulseStrength.value = 0.3
    if (syncCount.value > 10) runDeepen()
  }
}

function stopSync() {
  if (phase.value !== 'coherence') return

  const holdDuration = Tone.getTransport().seconds - syncStartTime
  isSyncing.value = false

  const accuracy = 1 - Math.min(Math.abs(holdDuration - INHALE_TIME) / INHALE_TIME, 1)
  coherenceScore.value = Math.min(
    100,
    Math.round(coherenceScore.value * 0.7 + accuracy * 100 * 0.3)
  )

  tunnelPulseStrength.value = 0.3
  syncCount.value++
  progress.value = Math.min(progress.value + 5, 100)

  if (coherenceScore.value > 70 && syncCount.value > 5) {
    runDeepen()
  }
}

async function toggleBaselineModulator() {
  if (baselineModulatorActive.value) stopBaselineModulator()
  else await startBaselineModulator()
}

async function togglePtosisInducer() {
  if (ptosisInducerActive.value) stopPtosisInducer()
  else await startPtosisInducer()
}

async function toggleAVSync(onFlash?: (flash: boolean) => void) {
  if (avSyncActive.value) stopAVSync()
  else await startAVSync(onFlash)
}

// ── Phase-aware visual accent ────────────────────────────────────
// Used by WebAudio canvas to tint star trails and glow
const phaseAccent = computed(() => {
  switch (phase.value) {
    case 'induction': return '#4a90e2'   // cool blue
    case 'coherence': return '#4a90e2'   // blue (pulse-driven)
    case 'deepen':    return '#7b5ea7'   // deep violet
    case 'joy':       return '#e09040'   // warm amber
    case 'wake':      return '#e8d090'   // soft gold
    default:          return '#4a90e2'
  }
})

// Whether the current phase shows floating text (not the pacer UI)
const isNarrativePhase = computed(() =>
  ['induction', 'deepen', 'joy', 'wake'].includes(phase.value)
)

export function useTranceEngine() {
  return {
    // Reactive state (readonly where appropriate)
    phase: readonly(phase),
    sessionActive: readonly(sessionActive),
    coherenceScore: readonly(coherenceScore),
    progress: readonly(progress),
    isExpanding: readonly(isExpanding),
    currentInstruction: readonly(currentInstruction),
    isSyncing: readonly(isSyncing),
    tunnelPulseStrength, // writable — visual components decay this
    baselineModulatorActive: readonly(baselineModulatorActive),
    ptosisInducerActive: readonly(ptosisInducerActive),
    avSyncActive: readonly(avSyncActive),
    phaseAccent,
    isNarrativePhase,

    // Session control
    startSession,
    stopSession,
    windDown,
    startSync,
    stopSync,

    // Entrainment modules
    toggleBaselineModulator,
    togglePtosisInducer,
    toggleAVSync,
  }
}
