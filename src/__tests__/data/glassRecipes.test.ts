import { describe, it, expect } from 'vitest'
import { GLASS_RECIPES } from '@/data/glassRecipes'
import { LEARN_TOPICS } from '@/data/learn'

const VALID_SLUGS = new Set(LEARN_TOPICS.map((t) => t.slug))

describe('GLASS_RECIPES', () => {
  it('every recipe build() returns a fully-formed composition', () => {
    for (const recipe of GLASS_RECIPES) {
      const comp = recipe.build()
      expect(comp.textLayers.length).toBeGreaterThan(0)
      for (const layer of comp.textLayers) {
        expect(layer.id).toBeTruthy()
        expect(layer.content.length).toBeGreaterThan(0)
        expect(['persistent', 'sequence', 'subliminal']).toContain(layer.timing.mode)
      }
      expect(comp.binaural.enabled).toBe(true)
      expect(['preset', 'journey']).toContain(comp.binaural.mode)
      if (comp.binaural.mode === 'journey') {
        expect(comp.binaural.journey.length).toBeGreaterThan(0)
      }
    }
  })

  it('build() returns fresh, unshared references each call', () => {
    const a = GLASS_RECIPES[0].build()
    const b = GLASS_RECIPES[0].build()
    expect(a.textLayers).not.toBe(b.textLayers)
    expect(a.binaural).not.toBe(b.binaural)
  })

  it('every learnSlug resolves to a real /learn article', () => {
    for (const recipe of GLASS_RECIPES) {
      if (recipe.learnSlug) {
        expect(VALID_SLUGS.has(recipe.learnSlug)).toBe(true)
      }
    }
  })
})
