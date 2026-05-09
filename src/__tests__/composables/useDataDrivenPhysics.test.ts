import { describe, it, expect } from 'vitest'
import { buildPhysicsOptions, valenceToOrbDefs } from '@/composables/useDataDrivenPhysics'

describe('buildPhysicsOptions', () => {
  const profile = {
    top_artists: ['Artist A', 'Artist B'],
    genres: ['electronic', 'ambient', 'indie'],
    audio_avg: {
      energy: 0.7,
      valence: 0.45,
      danceability: 0.6,
      acousticness: 0.3,
      tempo: 128,
    },
  }
  const physicsCfg = {
    particleSpeed: 'audio_avg.energy',
    colorTemp: 'audio_avg.valence',
    particleCount: 'genres.length',
    pulseRate: 'audio_avg.tempo',
    sizeVariance: 'audio_avg.acousticness',
  }

  it('maps energy to clearAlpha (higher energy = crisper trail)', () => {
    const opts = buildPhysicsOptions(profile, physicsCfg, '#1db954')
    expect(opts.clearAlpha).toBeGreaterThan(0.06)
    expect(opts.clearAlpha).toBeLessThan(0.2)
  })

  it('maps genre count to particleCount', () => {
    const opts = buildPhysicsOptions(profile, physicsCfg, '#1db954')
    // 3 genres → 80 + 3*20 = 140
    expect(opts.particleCount).toBe(140)
  })

  it('maps energy to mouseAttractForce', () => {
    const opts = buildPhysicsOptions(profile, physicsCfg, '#1db954')
    // energy 0.7 → 0.25 + 0.7*0.6 = 0.67
    expect(opts.mouseAttractForce).toBeCloseTo(0.67, 1)
  })

  it('falls back to defaults when profile is empty', () => {
    const empty = { top_artists: [], genres: [], audio_avg: {} }
    const opts = buildPhysicsOptions(empty, physicsCfg, '#1db954')
    expect(opts.particleCount).toBe(80)
    expect(opts.orbDefs.length).toBeGreaterThan(0)
  })
})

describe('valenceToOrbDefs', () => {
  it('returns cool colors for low valence', () => {
    const defs = valenceToOrbDefs(0.2, '#1db954')
    expect(defs[0].b).toBeGreaterThan(defs[0].r)
  })

  it('returns warm colors for high valence', () => {
    const defs = valenceToOrbDefs(0.8, '#1db954')
    expect(defs[0].r).toBeGreaterThan(defs[0].b)
  })

  it('uses provider color for mid valence', () => {
    const defs = valenceToOrbDefs(0.55, '#1db954')
    expect(defs[0].g).toBeGreaterThan(100)
  })
})
