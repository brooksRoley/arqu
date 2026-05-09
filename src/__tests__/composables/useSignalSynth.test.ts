import { describe, it, expect } from 'vitest'
import { buildSynthConfig, pickChord } from '@/composables/useSignalSynth'

describe('buildSynthConfig', () => {
  it('clamps BPM to 60-180 range', () => {
    const cfg = buildSynthConfig({ tempo: 30, energy: 0.5, valence: 0.5, danceability: 0.5, acousticness: 0.5 })
    expect(cfg.bpm).toBe(60)
    const cfg2 = buildSynthConfig({ tempo: 250, energy: 0.5, valence: 0.5, danceability: 0.5, acousticness: 0.5 })
    expect(cfg2.bpm).toBe(180)
  })

  it('maps energy to active voices', () => {
    const low = buildSynthConfig({ tempo: 120, energy: 0.2, valence: 0.5, danceability: 0.5, acousticness: 0.5 })
    expect(low.voices).toEqual(['kick'])

    const mid = buildSynthConfig({ tempo: 120, energy: 0.4, valence: 0.5, danceability: 0.5, acousticness: 0.5 })
    expect(mid.voices).toEqual(['kick', 'hat'])

    const high = buildSynthConfig({ tempo: 120, energy: 0.6, valence: 0.5, danceability: 0.5, acousticness: 0.5 })
    expect(high.voices).toEqual(['kick', 'hat', 'bass'])

    const full = buildSynthConfig({ tempo: 120, energy: 0.8, valence: 0.5, danceability: 0.5, acousticness: 0.5 })
    expect(full.voices).toEqual(['kick', 'hat', 'bass', 'snare'])
  })

  it('maps acousticness to filter cutoff', () => {
    const warm = buildSynthConfig({ tempo: 120, energy: 0.5, valence: 0.5, danceability: 0.5, acousticness: 0.9 })
    expect(warm.filterCutoff).toBeLessThan(1500)

    const bright = buildSynthConfig({ tempo: 120, energy: 0.5, valence: 0.5, danceability: 0.5, acousticness: 0.1 })
    expect(bright.filterCutoff).toBeGreaterThan(5000)
  })

  it('maps danceability to swing', () => {
    const straight = buildSynthConfig({ tempo: 120, energy: 0.5, valence: 0.5, danceability: 0.0, acousticness: 0.5 })
    expect(straight.swing).toBe(0)

    const groovy = buildSynthConfig({ tempo: 120, energy: 0.5, valence: 0.5, danceability: 1.0, acousticness: 0.5 })
    expect(groovy.swing).toBeCloseTo(0.6, 1)
  })
})

describe('pickChord', () => {
  it('returns minor pentatonic notes for low valence', () => {
    const chord = pickChord(0.2)
    expect(chord).toContain('C4')
    expect(chord).toContain('Eb4')
  })

  it('returns major notes for high valence', () => {
    const chord = pickChord(0.8)
    expect(chord).toContain('C4')
    expect(chord).toContain('E4')
  })

  it('returns dorian notes for mid valence', () => {
    const chord = pickChord(0.5)
    expect(chord).toContain('C4')
    expect(chord).toContain('Eb4')
    expect(chord).toContain('G4')
  })
})
