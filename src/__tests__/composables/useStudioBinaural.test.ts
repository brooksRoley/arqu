import { describe, it, expect } from 'vitest'
import { fitJourney, phaseAtTime, BANDS } from '@/composables/useStudioBinaural'

describe('fitJourney — auto-fit to media length', () => {
  const phases = [
    { band: 'alpha' as const, durationS: 60 },
    { band: 'theta' as const, durationS: 60 },
  ]

  it('scales authored durations to fill the media length', () => {
    const plan = fitJourney(phases, 30) // total 120 authored → fit into 30s
    expect(plan).toHaveLength(2)
    expect(plan[0].startS).toBeCloseTo(0, 5)
    expect(plan[0].endS).toBeCloseTo(15, 5)
    expect(plan[1].startS).toBeCloseTo(15, 5)
    expect(plan[1].endS).toBeCloseTo(30, 5)
  })

  it('maps each phase band to its beat/carrier', () => {
    const plan = fitJourney(phases, 120)
    expect(plan[0].beatHz).toBe(BANDS.alpha.beatHz)
    expect(plan[0].carrierHz).toBe(BANDS.alpha.carrierHz)
    expect(plan[1].beatHz).toBe(BANDS.theta.beatHz)
  })

  it('uses authored durations when total is unknown (0)', () => {
    const plan = fitJourney(phases, 0)
    expect(plan[0].endS).toBeCloseTo(60, 5)
    expect(plan[1].endS).toBeCloseTo(120, 5)
  })

  it('returns empty for no phases', () => {
    expect(fitJourney([], 60)).toEqual([])
  })
})

describe('phaseAtTime', () => {
  const plan = fitJourney(
    [
      { band: 'alpha', durationS: 10 },
      { band: 'theta', durationS: 10 },
      { band: 'delta', durationS: 10 },
    ],
    30,
  )

  it('finds the phase covering a time', () => {
    expect(phaseAtTime(plan, 0)).toBe(0)
    expect(phaseAtTime(plan, 9.9)).toBe(0)
    expect(phaseAtTime(plan, 10)).toBe(1)
    expect(phaseAtTime(plan, 25)).toBe(2)
  })

  it('holds the last phase past the end', () => {
    expect(phaseAtTime(plan, 999)).toBe(2)
  })

  it('clamps negative time to the first phase', () => {
    expect(phaseAtTime(plan, -5)).toBe(0)
  })

  it('returns -1 for an empty plan', () => {
    expect(phaseAtTime([], 5)).toBe(-1)
  })
})
