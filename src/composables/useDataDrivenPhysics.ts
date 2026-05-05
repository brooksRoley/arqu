import { type Ref } from 'vue'
import { useCosmicPhysics, type OrbDef, type CosmicConfig } from './useCosmicPhysics'
import { resolveField } from '@/config/connectorConfig'

// ── Valence → color palette ────────────────────────────────────────────────

const COOL_PALETTE: OrbDef[] = [
  { r: 26, g: 82, b: 118 },   // deep blue
  { r: 36, g: 113, b: 163 },  // steel blue
  { r: 72, g: 201, b: 176 },  // teal
  { r: 46, g: 134, b: 193 },  // sky
]

const PURPLE_PALETTE: OrbDef[] = [
  { r: 125, g: 60, b: 152 },  // purple
  { r: 165, g: 105, b: 189 }, // magenta
  { r: 195, g: 155, b: 211 }, // lavender
  { r: 142, g: 68, b: 173 },  // violet
]

const WARM_PALETTE: OrbDef[] = [
  { r: 243, g: 156, b: 18 },  // amber
  { r: 231, g: 76, b: 60 },   // coral
  { r: 241, g: 148, b: 138 }, // warm pink
  { r: 245, g: 176, b: 65 },  // gold
]

function hexToRgb(hex: string): OrbDef {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return { r, g, b }
}

function providerPalette(hex: string): OrbDef[] {
  const base = hexToRgb(hex)
  return [
    base,
    { r: Math.max(0, base.r - 40), g: Math.max(0, base.g - 20), b: Math.min(255, base.b + 30) },
    { r: Math.min(255, base.r + 30), g: Math.max(0, base.g - 30), b: Math.max(0, base.b - 20) },
    { r: Math.max(0, base.r - 20), g: Math.min(255, base.g + 40), b: Math.min(255, base.b + 20) },
  ]
}

export function valenceToOrbDefs(valence: number, providerHex: string): OrbDef[] {
  if (valence < 0.3) return COOL_PALETTE
  if (valence < 0.5) return PURPLE_PALETTE
  if (valence <= 0.7) return providerPalette(providerHex)
  return WARM_PALETTE
}

// ── Build physics options from profile data ────────────────────────────────

interface PhysicsFieldMap {
  particleSpeed: string
  colorTemp: string
  particleCount: string
  pulseRate: string
  sizeVariance?: string
}

export function buildPhysicsOptions(
  profile: Record<string, unknown>,
  physicsCfg: PhysicsFieldMap,
  providerHex: string,
): Required<CosmicConfig> {
  const energy = Number(resolveField(profile, physicsCfg.particleSpeed) ?? 0.5)
  const valence = Number(resolveField(profile, physicsCfg.colorTemp) ?? 0.5)
  const genreCount = Number(resolveField(profile, physicsCfg.particleCount) ?? 0)
  const tempo = Number(resolveField(profile, physicsCfg.pulseRate) ?? 120)

  const normTempo = Math.min(1, Math.max(0, (tempo - 60) / 140))

  return {
    orbDefs: valenceToOrbDefs(valence, providerHex),
    particleCount: 80 + Math.round(genreCount * 20),
    starCount: 120,
    clearAlpha: 0.055 + energy * 0.06 + normTempo * 0.02,
    enableKeyboard: false,
    enableMouseInteract: true,
    mouseAttractForce: 0.25 + energy * 0.6,
  }
}

// ── Composable ─────────────────────────────────────────────────────────────

export function useDataDrivenPhysics(
  canvasRef: Ref<HTMLCanvasElement | undefined>,
  profile: Record<string, unknown> | null,
  physicsCfg: PhysicsFieldMap,
  providerHex: string,
) {
  const options = profile
    ? buildPhysicsOptions(profile, physicsCfg, providerHex)
    : {
        orbDefs: providerPalette(providerHex),
        particleCount: 180,
        starCount: 120,
        clearAlpha: 0.08,
        enableKeyboard: false,
        enableMouseInteract: true,
        mouseAttractForce: 0.6,
      }

  const cosmic = useCosmicPhysics(canvasRef, options)

  return {
    ...cosmic,
    valence: profile ? Number(resolveField(profile, physicsCfg.colorTemp) ?? 0.5) : 0.5,
  }
}
