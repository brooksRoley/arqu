import { ref, readonly } from 'vue'

/**
 * Raw Web Audio API binaural beat engine.
 *
 * Two sine oscillators (left / right channel) offset by `beatFreq` Hz.
 * The brain perceives the difference as a binaural beat at the gamma frequency.
 *
 *   L = carrier - beatFreq/2
 *   R = carrier + beatFreq/2
 *   Perceived beat = R - L = beatFreq
 */
class BinauralEngine {
  ctx: AudioContext | null = null
  oscLeft: OscillatorNode | null = null
  oscRight: OscillatorNode | null = null
  masterGain: GainNode | null = null
  merger: ChannelMergerNode | null = null
  analyser: AnalyserNode | null = null
  carrier = 220
  beatFreq = 40
  started = false

  init() {
    this.ctx = new (window.AudioContext || (window as any).webkitAudioContext)()

    this.masterGain = this.ctx.createGain()
    this.masterGain.gain.value = 0.12

    this.analyser = this.ctx.createAnalyser()
    this.analyser.fftSize = 256

    this.merger = this.ctx.createChannelMerger(2)

    // Left ear oscillator
    this.oscLeft = this.ctx.createOscillator()
    const gainL = this.ctx.createGain()
    this.oscLeft.type = 'sine'
    this.oscLeft.frequency.value = this.carrier - this.beatFreq / 2
    gainL.gain.value = 1
    this.oscLeft.connect(gainL)
    gainL.connect(this.merger, 0, 0)

    // Right ear oscillator
    this.oscRight = this.ctx.createOscillator()
    const gainR = this.ctx.createGain()
    this.oscRight.type = 'sine'
    this.oscRight.frequency.value = this.carrier + this.beatFreq / 2
    gainR.gain.value = 1
    this.oscRight.connect(gainR)
    gainR.connect(this.merger, 0, 1)

    this.merger.connect(this.masterGain)
    this.masterGain.connect(this.analyser)
    this.analyser.connect(this.ctx.destination)

    this.oscLeft.start()
    this.oscRight.start()
    this.started = true
  }

  setBeat(beatHz: number, carrierHz?: number, rampTime = 1.5) {
    if (!this.started || !this.ctx || !this.oscLeft || !this.oscRight) return
    const now = this.ctx.currentTime
    this.carrier = carrierHz ?? this.carrier
    this.beatFreq = beatHz

    this.oscLeft.frequency.cancelScheduledValues(now)
    this.oscRight.frequency.cancelScheduledValues(now)
    this.oscLeft.frequency.setValueAtTime(this.oscLeft.frequency.value, now)
    this.oscRight.frequency.setValueAtTime(this.oscRight.frequency.value, now)
    this.oscLeft.frequency.linearRampToValueAtTime(this.carrier - beatHz / 2, now + rampTime)
    this.oscRight.frequency.linearRampToValueAtTime(this.carrier + beatHz / 2, now + rampTime)
  }

  setVolume(val: number) {
    if (!this.started || !this.masterGain || !this.ctx) return
    const now = this.ctx.currentTime
    this.masterGain.gain.cancelScheduledValues(now)
    this.masterGain.gain.setValueAtTime(this.masterGain.gain.value, now)
    this.masterGain.gain.linearRampToValueAtTime(val, now + 0.3)
  }

  getWaveformData(): Uint8Array | null {
    if (!this.analyser) return null
    const d = new Uint8Array(this.analyser.frequencyBinCount)
    this.analyser.getByteTimeDomainData(d)
    return d
  }

  destroy() {
    try { this.oscLeft?.stop() } catch { /* already stopped */ }
    try { this.oscRight?.stop() } catch { /* already stopped */ }
    try { this.ctx?.close() } catch { /* already closed */ }
    this.started = false
    this.ctx = null
    this.oscLeft = null
    this.oscRight = null
    this.masterGain = null
    this.merger = null
    this.analyser = null
  }
}

// ── Singleton ──
let engine: BinauralEngine | null = null
const initialized = ref(false)
const volume = ref(12)

export function useBinauralEngine() {
  function init() {
    if (engine?.started) return
    engine = new BinauralEngine()
    engine.init()
    initialized.value = true
  }

  function setBeat(beatHz: number, carrierHz?: number, rampTime?: number) {
    engine?.setBeat(beatHz, carrierHz, rampTime)
  }

  function setVolume(val: number) {
    volume.value = val
    engine?.setVolume(val / 100 * 0.25)
  }

  function getWaveformData(): Uint8Array | null {
    return engine?.getWaveformData() ?? null
  }

  function destroy() {
    engine?.destroy()
    engine = null
    initialized.value = false
  }

  return {
    initialized: readonly(initialized),
    volume,
    init,
    setBeat,
    setVolume,
    getWaveformData,
    destroy,
  }
}
