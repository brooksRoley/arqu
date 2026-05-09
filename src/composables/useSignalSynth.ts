import { ref } from 'vue'

// ── Types ─────────────────────────────────────────────────────────────────────

export interface AudioMetrics {
  tempo: number
  energy: number
  valence: number
  danceability: number
  acousticness: number
}

export interface SynthConfig {
  bpm: number
  voices: string[]
  filterCutoff: number
  swing: number
}

// ── Pure config builders (testable without AudioContext) ───────────────────────

/**
 * Maps Spotify-style audio metrics to a synth configuration object.
 * - BPM clamped to [60, 180]
 * - energy < 0.3 → ['kick'], < 0.5 → add 'hat', < 0.7 → add 'bass', else add 'snare'
 * - acousticness → filterCutoff: high acousticness = warm (low cutoff), low = bright (high cutoff)
 * - danceability → swing: 0 at 0.0, 0.6 at 1.0
 */
export function buildSynthConfig(metrics: AudioMetrics): SynthConfig {
  const { tempo, energy, acousticness, danceability } = metrics

  // Clamp BPM to [60, 180]
  const bpm = Math.min(180, Math.max(60, tempo))

  // Energy → voices (cumulative layers)
  const voices: string[] = ['kick']
  if (energy >= 0.3) voices.push('hat')
  if (energy >= 0.5) voices.push('bass')
  if (energy >= 0.7) voices.push('snare')

  // Acousticness → filterCutoff (power curve for more dramatic spread)
  // High acousticness (acoustic = warm) → low cutoff
  // Low acousticness (electronic = bright) → high cutoff
  const filterCutoff = 200 + Math.pow(1 - acousticness, 1.5) * 8000

  // Danceability → swing [0, 0.6]
  const swing = danceability * 0.6

  return { bpm, voices, filterCutoff, swing }
}

/**
 * Maps valence to a chord voicing.
 * - < 0.4: minor pentatonic (C Eb G Bb)
 * - 0.4–0.6: dorian (C Eb G Bb D)
 * - > 0.6: major (C E G B D)
 */
export function pickChord(valence: number): string[] {
  if (valence < 0.4) {
    // Minor pentatonic
    return ['C4', 'Eb4', 'G4', 'Bb4']
  } else if (valence <= 0.6) {
    // Dorian (minor 3rd, natural 6th)
    return ['C4', 'Eb4', 'G4', 'Bb4', 'D5']
  } else {
    // Major
    return ['C4', 'E4', 'G4', 'B4', 'D5']
  }
}

// ── Composable (lazy Tone.js instantiation) ───────────────────────────────────

type ToneModule = typeof import('tone')

// Scale notes for random hit triggers
const SCALE_NOTES = ['C3', 'D3', 'E3', 'G3', 'A3', 'C4', 'D4', 'E4', 'G4', 'A4']

function pickRandom<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)]
}

export function useSignalSynth(metrics: AudioMetrics) {
  const isStarted = ref(false)
  const isMuted = ref(false)

  const cfg = buildSynthConfig(metrics)

  // Lazy Tone.js handles — created on first start()
  let Tone: ToneModule | null = null
  let kick: InstanceType<ToneModule['MembraneSynth']> | null = null
  let hat: InstanceType<ToneModule['NoiseSynth']> | null = null
  let snare: InstanceType<ToneModule['NoiseSynth']> | null = null
  let bass: InstanceType<ToneModule['MonoSynth']> | null = null
  let pad: InstanceType<ToneModule['PolySynth']> | null = null
  let hit: InstanceType<ToneModule['MembraneSynth']> | null = null

  let filter: InstanceType<ToneModule['Filter']> | null = null
  let panner: InstanceType<ToneModule['Panner']> | null = null
  let gain: InstanceType<ToneModule['Gain']> | null = null

  // Sequences
  const sequences: { stop(): void; dispose(): void }[] = []

  async function ensureTone(): Promise<ToneModule> {
    if (!Tone) {
      Tone = await import('tone')
    }
    return Tone
  }

  async function buildGraph(T: ToneModule) {
    // Master chain: synths → panner → filter → gain → destination
    gain = new T.Gain(0.8).toDestination()
    filter = new T.Filter(cfg.filterCutoff, 'lowpass').connect(gain)
    panner = new T.Panner(0).connect(filter)

    // Kick
    kick = new T.MembraneSynth({
      pitchDecay: 0.05,
      octaves: 6,
      envelope: { attack: 0.001, decay: 0.3, sustain: 0, release: 0.1 },
    }).connect(panner)

    // Hat
    hat = new T.NoiseSynth({
      noise: { type: 'white' },
      envelope: { attack: 0.001, decay: 0.05, sustain: 0, release: 0.02 },
    }).connect(panner)

    // Snare
    snare = new T.NoiseSynth({
      noise: { type: 'pink' },
      envelope: { attack: 0.001, decay: 0.15, sustain: 0, release: 0.05 },
    }).connect(panner)

    // Bass
    bass = new T.MonoSynth({
      oscillator: { type: 'triangle' },
      envelope: { attack: 0.01, decay: 0.2, sustain: 0.3, release: 0.1 },
      filterEnvelope: { attack: 0.01, decay: 0.1, sustain: 0.5, release: 0.1, baseFrequency: 100, octaves: 2 },
    }).connect(panner)

    // Pad
    pad = new T.PolySynth(T.FMSynth, {
      volume: -18,
      harmonicity: 3,
      modulationIndex: 2,
      envelope: { attack: 0.5, decay: 0.5, sustain: 0.8, release: 2 },
    }).connect(panner)

    // Hit (one-shot)
    hit = new T.MembraneSynth({
      pitchDecay: 0.08,
      octaves: 4,
      envelope: { attack: 0.001, decay: 0.4, sustain: 0, release: 0.1 },
    }).connect(panner)
  }

  function buildSequences(T: ToneModule) {
    const transport = T.getTransport()
    transport.bpm.value = cfg.bpm

    const sixteenth = '16n'
    const eighth = '8n'

    // Kick pattern — every 2 beats (on the 1 and 3 in 4/4)
    const kickSeq = new T.Sequence(
      (time) => {
        if (cfg.voices.includes('kick')) {
          kick?.triggerAttackRelease('C1', '8n', time)
        }
      },
      [0, null, null, null, null, null, null, null, 0, null, null, null, null, null, null, null],
      sixteenth,
    )
    kickSeq.start(0)
    sequences.push(kickSeq)

    // Hat pattern — every 8th note
    if (cfg.voices.includes('hat')) {
      const hatSeq = new T.Sequence(
        (time) => {
          hat?.triggerAttackRelease('8n', time)
        },
        [0, 0, 0, 0, 0, 0, 0, 0],
        eighth,
      )
      hatSeq.start(0)
      sequences.push(hatSeq)
    }

    // Bass — 8th note walking on C2
    if (cfg.voices.includes('bass')) {
      const bassSeq = new T.Sequence(
        (time) => {
          bass?.triggerAttackRelease('C2', '8n', time)
        },
        [0, null, 0, null, 0, null, 0, null],
        eighth,
      )
      bassSeq.start(0)
      sequences.push(bassSeq)
    }

    // Snare — beats 2 and 4
    if (cfg.voices.includes('snare')) {
      const snareSeq = new T.Sequence(
        (time) => {
          snare?.triggerAttackRelease('8n', time)
        },
        [null, null, null, null, 0, null, null, null, null, null, null, null, 0, null, null, null],
        sixteenth,
      )
      snareSeq.start(0)
      sequences.push(snareSeq)
    }

    // Pad — chord every 2 bars
    const chord = pickChord(metrics.valence)
    const padSeq = new T.Sequence(
      (time) => {
        pad?.triggerAttackRelease(chord, '2m', time)
      },
      [0],
      '2m',
    )
    padSeq.start(0)
    sequences.push(padSeq)
  }

  async function start() {
    if (isStarted.value) return
    const T = await ensureTone()
    await T.start()
    await buildGraph(T)
    buildSequences(T)
    T.getTransport().start()
    isStarted.value = true
  }

  function stop() {
    if (!isStarted.value || !Tone) return
    Tone.getTransport().stop()
    sequences.forEach((s) => s.stop())
    isStarted.value = false
  }

  async function toggle() {
    if (isStarted.value) {
      stop()
    } else {
      await start()
    }
  }

  function setVolume(n: number) {
    if (gain) gain.gain.rampTo(n, 0.1)
  }

  function setPan(n: number) {
    if (panner) (panner.pan as { rampTo(v: number, t: number): void }).rampTo(n, 0.1)
  }

  function spikeResonance(intensity: number) {
    if (!filter || !Tone) return
    const target = cfg.filterCutoff * (1 + intensity * 4)
    filter.frequency.rampTo(target, 0.05)
    // Decay back
    filter.frequency.rampTo(cfg.filterCutoff, 0.5)
  }

  function triggerHit() {
    if (!hit) return
    const note = pickRandom(SCALE_NOTES)
    hit.triggerAttackRelease(note, '16n')
  }

  function dispose() {
    stop()
    sequences.forEach((s) => s.dispose())
    sequences.length = 0
    kick?.dispose()
    hat?.dispose()
    snare?.dispose()
    bass?.dispose()
    pad?.dispose()
    hit?.dispose()
    filter?.dispose()
    panner?.dispose()
    gain?.dispose()
    kick = hat = snare = bass = pad = hit = filter = panner = gain = null
    Tone = null
    isStarted.value = false
  }

  return {
    isStarted,
    isMuted,
    start,
    stop,
    toggle,
    setVolume,
    setPan,
    spikeResonance,
    triggerHit,
    dispose,
  }
}
