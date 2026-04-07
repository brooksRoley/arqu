<script setup lang="ts">
import { ref, reactive, computed } from 'vue'

// ── Body type toggle ──────────────────────────────────────────────
type BodyType = 'female' | 'male'
const bodyType = ref<BodyType>('female')

// ── Active zone for highlight ─────────────────────────────────────
const activeZone = ref<string | null>(null)
function selectZone(zone: string) { activeZone.value = zone }
function clearZone() { activeZone.value = null }

// ── Body measurements ─────────────────────────────────────────────
const body = reactive({
  height: 68,        // inches (56–82 inclusive range)
  build: 5,          // 1–10
  chest: 40,         // unisex chest/bust (26–58)
  waist: 34,         // (22–58)
  hips: 40,          // (28–64)
  shoulders: 18,     // shoulder width in inches (14–24)
})

// ── Appearance ────────────────────────────────────────────────────
const skinColor = ref('#C68642')
const skinShadow = ref('#A0522D')
const hairColor = ref('#3B1F0A')
const hairLength = ref<'short' | 'medium' | 'long'>('medium')

const skinTones = [
  { color: '#FDDBB4', shadow: '#E8B88A' },
  { color: '#EDB98A', shadow: '#C88B5A' },
  { color: '#C68642', shadow: '#A0522D' },
  { color: '#8D5524', shadow: '#6B3A0F' },
  { color: '#4A2912', shadow: '#2E1508' },
  { color: '#FEE0C0', shadow: '#ECBF98' },
]

const hairColors = ['#3B1F0A', '#6B3A0F', '#C49A3C', '#E8D5A3', '#1A1A1A', '#8B0000', '#6B478B', '#4A90D9']

// ── Suit colors (shared) ──────────────────────────────────────────
const suitColor = ref('#2E86AB')
const suitColorDark = ref('#1A5276')

const suitOptions = [
  { color: '#2E86AB', dark: '#1A5276' },
  { color: '#C0458A', dark: '#8B1A5E' },
  { color: '#E8453C', dark: '#B03030' },
  { color: '#27AE60', dark: '#1A7A42' },
  { color: '#F39C12', dark: '#B07A0A' },
  { color: '#1A1A2E', dark: '#0D0D1A' },
  { color: '#FFFFFF', dark: '#C8C8C8' },
  { color: '#E8C3E8', dark: '#C090C0' },
]

// ── Female suit options ───────────────────────────────────────────
const femaleSuit = reactive({
  topStyle: 'underwire' as 'underwire' | 'bralette' | 'bandeau' | 'halter',
  rise: 'mid' as 'low' | 'mid' | 'high' | 'ultra',
  coverage: 'full' as 'cheeky' | 'moderate' | 'full' | 'boy-short',
})
const topStyles = ['underwire', 'bralette', 'bandeau', 'halter'] as const
const riseOptions = ['low', 'mid', 'high', 'ultra'] as const
const coverageOptions = ['cheeky', 'moderate', 'full', 'boy-short'] as const

// ── Male suit options ─────────────────────────────────────────────
const maleSuit = reactive({
  top: 'none' as 'none' | 'rash-short' | 'rash-long' | 'tank',
  bottom: 'board-knee' as 'board-above' | 'board-knee' | 'board-below' | 'trunk',
  wetsuit: 'none' as 'none' | 'shorty' | 'spring' | 'full',
})
const maleTopOptions = [
  { value: 'none', label: 'None' },
  { value: 'rash-short', label: 'Rash Guard' },
  { value: 'rash-long', label: 'Long Sleeve' },
  { value: 'tank', label: 'Tank' },
] as const
const maleBottomOptions = [
  { value: 'trunk', label: 'Trunks' },
  { value: 'board-above', label: 'Above Knee' },
  { value: 'board-knee', label: 'Knee' },
  { value: 'board-below', label: 'Below Knee' },
] as const
const wetsuitOptions = [
  { value: 'none', label: 'None' },
  { value: 'shorty', label: 'Shorty' },
  { value: 'spring', label: 'Spring' },
  { value: 'full', label: 'Full' },
] as const

// ── Layout constants ──────────────────────────────────────────────
const cx = 150

const heightScale = computed(() => 0.82 + (body.height - 56) / 26 * 0.36)
const buildScale = computed(() => 0.78 + (body.build - 1) / 9 * 0.56)

const svgHeight = computed(() => Math.round(720 * heightScale.value))

const isMale = computed(() => bodyType.value === 'male')

// Shoulder width: males tend wider, females narrower — driven by slider
const shoulderMul = computed(() => body.shoulders / 18)

// Derived widths in SVG space
const chestW = computed(() => (body.chest / 38) * 68 * buildScale.value)
const waistW = computed(() => (body.waist / 32) * 52 * buildScale.value)
const hipW = computed(() => (body.hips / 42) * 78 * buildScale.value)
const shoulderW = computed(() => chestW.value * 0.95 * shoulderMul.value)

// Key Y positions
const headH = computed(() => 36 * heightScale.value)
const headW = computed(() => 26)
const headY = computed(() => 46 * heightScale.value)
const neckW = computed(() => isMale.value ? 26 : 22)
const neckH = computed(() => 18 * heightScale.value)

const shoulderY = computed(() => headY.value + headH.value + neckH.value)
const chestY = computed(() => shoulderY.value + 18 * heightScale.value)
const underchestY = computed(() => {
  const bustFactor = isMale.value ? 0.3 : 0.5
  return chestY.value + 54 * heightScale.value * (body.chest / 38) * bustFactor + 20
})
const waistY = computed(() => underchestY.value + 40 * heightScale.value)
const hipTopY = computed(() => waistY.value + 20 * heightScale.value)
const hipBottomY = computed(() => hipTopY.value + 70 * heightScale.value)
const crotchY = computed(() => hipBottomY.value)
const kneeY = computed(() => crotchY.value + 100 * heightScale.value)
const legBottom = computed(() => crotchY.value + 200 * heightScale.value)

// ── Hair paths ────────────────────────────────────────────────────
const hairPath = computed(() => {
  const hy = headY.value
  const hh = headH.value
  const hw = headW.value

  if (hairLength.value === 'short') {
    // Close crop — just covers top of head
    return `
      M ${cx - hw * 1.0} ${hy - hh * 0.3}
      Q ${cx - hw * 0.6} ${hy - hh * 1.1} ${cx} ${hy - hh * 1.0}
      Q ${cx + hw * 0.6} ${hy - hh * 1.1} ${cx + hw * 1.0} ${hy - hh * 0.3}
      Q ${cx + hw * 0.85} ${hy - hh * 0.7} ${cx} ${hy - hh * 0.65}
      Q ${cx - hw * 0.85} ${hy - hh * 0.7} ${cx - hw * 1.0} ${hy - hh * 0.3}
      Z
    `
  }

  if (hairLength.value === 'long') {
    // Flows past shoulders
    const flowY = shoulderY.value + 40 * heightScale.value
    return `
      M ${cx - hw * 1.15} ${hy - hh * 0.2}
      Q ${cx - hw * 0.7} ${hy - hh * 1.15} ${cx} ${hy - hh * 1.05}
      Q ${cx + hw * 0.7} ${hy - hh * 1.15} ${cx + hw * 1.15} ${hy - hh * 0.2}
      Q ${cx + hw * 1.3} ${hy + hh * 0.5} ${cx + hw * 1.1} ${flowY}
      Q ${cx + hw * 0.6} ${flowY + 20} ${cx} ${flowY + 10}
      Q ${cx - hw * 0.6} ${flowY + 20} ${cx - hw * 1.1} ${flowY}
      Q ${cx - hw * 1.3} ${hy + hh * 0.5} ${cx - hw * 1.15} ${hy - hh * 0.2}
      Z
    `
  }

  // Medium — sits around head/neck
  return `
    M ${cx - hw * 1.1} ${hy - hh * 0.15}
    Q ${cx - hw * 0.65} ${hy - hh * 1.12} ${cx} ${hy - hh * 1.02}
    Q ${cx + hw * 0.65} ${hy - hh * 1.12} ${cx + hw * 1.1} ${hy - hh * 0.15}
    Q ${cx + hw * 1.2} ${hy + hh * 0.4} ${cx + hw * 1.0} ${shoulderY.value - 4}
    Q ${cx + hw * 0.5} ${shoulderY.value + 8} ${cx} ${shoulderY.value + 4}
    Q ${cx - hw * 0.5} ${shoulderY.value + 8} ${cx - hw * 1.0} ${shoulderY.value - 4}
    Q ${cx - hw * 1.2} ${hy + hh * 0.4} ${cx - hw * 1.1} ${hy - hh * 0.15}
    Z
  `
})

// ── Body shape paths ──────────────────────────────────────────────
const shoulderPath = computed(() => {
  const sy = shoulderY.value
  const sw = shoulderW.value
  const ww = waistW.value

  if (isMale.value) {
    // Male: broader, squarer shoulders, V-taper to waist
    return `
      M ${cx - sw * 1.05} ${sy + 20}
      Q ${cx - sw * 1.1} ${sy - 4} ${cx - sw * 0.5} ${sy - 8}
      L ${cx + sw * 0.5} ${sy - 8}
      Q ${cx + sw * 1.1} ${sy - 4} ${cx + sw * 1.05} ${sy + 20}
      Q ${cx + ww * 0.7} ${waistY.value} ${cx + ww * 0.55} ${waistY.value}
      L ${cx - ww * 0.55} ${waistY.value}
      Q ${cx - ww * 0.7} ${waistY.value} ${cx - sw * 1.05} ${sy + 20}
      Z
    `
  }

  // Female: rounder shoulders, smoother curve
  return `
    M ${cx - sw} ${sy + 24}
    Q ${cx - sw * 1.05} ${sy} ${cx - sw * 0.55} ${sy - 6}
    L ${cx + sw * 0.55} ${sy - 6}
    Q ${cx + sw * 1.05} ${sy} ${cx + sw} ${sy + 24}
    Q ${cx + ww * 0.6} ${waistY.value} ${cx + ww / 2} ${waistY.value}
    L ${cx - ww / 2} ${waistY.value}
    Q ${cx - ww * 0.6} ${waistY.value} ${cx - sw} ${sy + 24}
    Z
  `
})

const torsoSkinPath = computed(() => {
  const bw = chestW.value / 2
  const ww = waistW.value / 2
  const hw = hipW.value / 2

  if (isMale.value) {
    // V-taper: chest wider than hips, straighter sides
    return `
      M ${cx - bw} ${chestY.value}
      Q ${cx - ww * 1.05} ${waistY.value} ${cx - ww} ${waistY.value}
      Q ${cx - hw * 0.95} ${hipTopY.value} ${cx - hw * 0.85} ${hipBottomY.value}
      L ${cx + hw * 0.85} ${hipBottomY.value}
      Q ${cx + hw * 0.95} ${hipTopY.value} ${cx + ww} ${waistY.value}
      Q ${cx + ww * 1.05} ${waistY.value} ${cx + bw} ${chestY.value}
      Z
    `
  }

  // Female: hourglass, wider hips
  return `
    M ${cx - bw} ${chestY.value}
    Q ${cx - ww * 1.1} ${waistY.value} ${cx - ww} ${waistY.value}
    Q ${cx - hw * 1.05} ${hipTopY.value} ${cx - hw} ${hipBottomY.value}
    L ${cx + hw} ${hipBottomY.value}
    Q ${cx + hw * 1.05} ${hipTopY.value} ${cx + ww} ${waistY.value}
    Q ${cx + ww * 1.1} ${waistY.value} ${cx + bw} ${chestY.value}
    Z
  `
})

const leftArmPath = computed(() => {
  const sw = shoulderW.value
  const armThick = isMale.value ? 20 * buildScale.value * 0.9 : 16 * buildScale.value * 0.85
  const ax = cx - sw
  return `
    M ${ax - armThick * 0.6} ${shoulderY.value + 12}
    Q ${ax - armThick} ${shoulderY.value + 60 * heightScale.value} ${ax - armThick * 0.5} ${waistY.value + 10}
    L ${ax + armThick * 0.4} ${waistY.value + 10}
    Q ${ax + armThick * 0.2} ${shoulderY.value + 60 * heightScale.value} ${ax + armThick * 0.6} ${shoulderY.value + 12}
    Z
  `
})

const rightArmPath = computed(() => {
  const sw = shoulderW.value
  const armThick = isMale.value ? 20 * buildScale.value * 0.9 : 16 * buildScale.value * 0.85
  const ax = cx + sw
  return `
    M ${ax + armThick * 0.6} ${shoulderY.value + 12}
    Q ${ax + armThick} ${shoulderY.value + 60 * heightScale.value} ${ax + armThick * 0.5} ${waistY.value + 10}
    L ${ax - armThick * 0.4} ${waistY.value + 10}
    Q ${ax - armThick * 0.2} ${shoulderY.value + 60 * heightScale.value} ${ax - armThick * 0.6} ${shoulderY.value + 12}
    Z
  `
})

const leftLegPath = computed(() => {
  const hw = hipW.value / 2
  const legThick = isMale.value ? hw * 0.56 : hw * 0.52
  const lx = cx - hw * 0.28
  return `
    M ${cx - hw * 0.05} ${crotchY.value}
    L ${cx - hw * 0.6} ${crotchY.value}
    Q ${lx - legThick * 0.55} ${crotchY.value + 80 * heightScale.value} ${lx - legThick * 0.45} ${legBottom.value}
    L ${lx + legThick * 0.35} ${legBottom.value}
    Q ${lx + legThick * 0.55} ${crotchY.value + 80 * heightScale.value} ${cx + hw * 0.05} ${crotchY.value}
    Z
  `
})

const rightLegPath = computed(() => {
  const hw = hipW.value / 2
  const legThick = isMale.value ? hw * 0.56 : hw * 0.52
  const lx = cx + hw * 0.28
  return `
    M ${cx + hw * 0.05} ${crotchY.value}
    L ${cx + hw * 0.6} ${crotchY.value}
    Q ${lx + legThick * 0.55} ${crotchY.value + 80 * heightScale.value} ${lx + legThick * 0.45} ${legBottom.value}
    L ${lx - legThick * 0.35} ${legBottom.value}
    Q ${lx - legThick * 0.55} ${crotchY.value + 80 * heightScale.value} ${cx - hw * 0.05} ${crotchY.value}
    Z
  `
})

// ── Female suit top path ──────────────────────────────────────────
const suitTopPath = computed(() => {
  const bw = chestW.value / 2
  const ww = waistW.value / 2
  const by = chestY.value
  const uby = underchestY.value
  const style = femaleSuit.topStyle

  if (style === 'bandeau') {
    const h = (uby - by) * 0.85
    return `
      M ${cx - bw * 1.02} ${by + 8}
      L ${cx + bw * 1.02} ${by + 8}
      L ${cx + bw * 0.95} ${by + h}
      Q ${cx + ww * 0.9} ${uby} ${cx} ${uby}
      Q ${cx - ww * 0.9} ${uby} ${cx - bw * 0.95} ${by + h}
      Z
    `
  }

  if (style === 'halter') {
    const neckPt = shoulderY.value - 16
    return `
      M ${cx} ${neckPt}
      L ${cx + bw * 1.0} ${by + 10}
      Q ${cx + bw * 0.9} ${uby} ${cx + ww * 0.5} ${uby}
      Q ${cx} ${uby + 6} ${cx - ww * 0.5} ${uby}
      Q ${cx - bw * 0.9} ${uby} ${cx - bw * 1.0} ${by + 10}
      Z
    `
  }

  if (style === 'bralette') {
    return `
      M ${cx - bw * 1.0} ${by + 14}
      Q ${cx - bw * 0.5} ${by - 4} ${cx} ${by + 2}
      Q ${cx + bw * 0.5} ${by - 4} ${cx + bw * 1.0} ${by + 14}
      Q ${cx + ww * 1.0} ${uby - 4} ${cx + ww * 0.7} ${uby}
      Q ${cx} ${uby + 8} ${cx - ww * 0.7} ${uby}
      Q ${cx - ww * 1.0} ${uby - 4} ${cx - bw * 1.0} ${by + 14}
      Z
    `
  }

  // underwire
  return `
    M ${cx - bw * 1.05} ${by + 16}
    Q ${cx - bw * 0.9} ${by - 8} ${cx - bw * 0.15} ${by + 6}
    Q ${cx} ${by - 2} ${cx + bw * 0.15} ${by + 6}
    Q ${cx + bw * 0.9} ${by - 8} ${cx + bw * 1.05} ${by + 16}
    Q ${cx + ww * 1.05} ${uby - 2} ${cx + ww * 0.65} ${uby}
    Q ${cx} ${uby + 6} ${cx - ww * 0.65} ${uby}
    Q ${cx - ww * 1.05} ${uby - 2} ${cx - bw * 1.05} ${by + 16}
    Z
  `
})

// ── Female suit bottom path ───────────────────────────────────────
const femaleSuitBottomPath = computed(() => {
  const hw = hipW.value / 2
  const ww = waistW.value / 2

  const riseOffset = { low: 30, mid: 14, high: 2, ultra: -8 }[femaleSuit.rise] ?? 14
  const topY = hipTopY.value + riseOffset
  const botY = hipBottomY.value
  const sideIn = { cheeky: 0.55, moderate: 0.72, full: 0.88, 'boy-short': 0.95 }[femaleSuit.coverage] ?? 0.88

  return `
    M ${cx - ww * 0.85} ${topY}
    Q ${cx - hw * 1.02} ${topY + (botY - topY) * 0.3} ${cx - hw * sideIn} ${botY - 4}
    Q ${cx - hw * 0.3} ${botY + 10} ${cx} ${botY + 8}
    Q ${cx + hw * 0.3} ${botY + 10} ${cx + hw * sideIn} ${botY - 4}
    Q ${cx + hw * 1.02} ${topY + (botY - topY) * 0.3} ${cx + ww * 0.85} ${topY}
    Q ${cx} ${topY - 8} ${cx - ww * 0.85} ${topY}
    Z
  `
})

// ── Male suit top (rash guard / tank) ─────────────────────────────
const maleTopPath = computed(() => {
  if (maleSuit.top === 'none') return ''

  const sw = shoulderW.value
  const ww = waistW.value / 2
  const sy = shoulderY.value
  const wy = waistY.value + 10

  if (maleSuit.top === 'tank') {
    // Sleeveless — narrower at shoulders, no arm coverage
    const tankSw = sw * 0.7
    return `
      M ${cx - tankSw} ${sy + 6}
      Q ${cx - tankSw * 0.4} ${sy - 4} ${cx} ${sy - 2}
      Q ${cx + tankSw * 0.4} ${sy - 4} ${cx + tankSw} ${sy + 6}
      Q ${cx + ww * 0.85} ${wy - 20} ${cx + ww * 0.7} ${wy}
      L ${cx - ww * 0.7} ${wy}
      Q ${cx - ww * 0.85} ${wy - 20} ${cx - tankSw} ${sy + 6}
      Z
    `
  }

  // Rash guard — covers shoulders and down arms
  const sleeveEnd = maleSuit.top === 'rash-long'
    ? waistY.value + 10
    : shoulderY.value + 50 * heightScale.value

  const armThick = 20 * buildScale.value * 0.9
  const lax = cx - sw
  const rax = cx + sw

  // Body portion
  const bodyPath = `
    M ${cx - sw * 1.05} ${sy + 6}
    Q ${cx - sw * 0.5} ${sy - 8} ${cx} ${sy - 6}
    Q ${cx + sw * 0.5} ${sy - 8} ${cx + sw * 1.05} ${sy + 6}
    Q ${cx + ww * 0.8} ${wy - 20} ${cx + ww * 0.65} ${wy}
    L ${cx - ww * 0.65} ${wy}
    Q ${cx - ww * 0.8} ${wy - 20} ${cx - sw * 1.05} ${sy + 6}
    Z
  `

  // Left sleeve
  const lSleeve = `
    M ${lax - armThick * 0.6} ${sy + 12}
    Q ${lax - armThick * 0.9} ${(sy + sleeveEnd) / 2} ${lax - armThick * 0.5} ${sleeveEnd}
    L ${lax + armThick * 0.4} ${sleeveEnd}
    Q ${lax + armThick * 0.2} ${(sy + sleeveEnd) / 2} ${lax + armThick * 0.5} ${sy + 12}
    Z
  `

  // Right sleeve
  const rSleeve = `
    M ${rax + armThick * 0.6} ${sy + 12}
    Q ${rax + armThick * 0.9} ${(sy + sleeveEnd) / 2} ${rax + armThick * 0.5} ${sleeveEnd}
    L ${rax - armThick * 0.4} ${sleeveEnd}
    Q ${rax - armThick * 0.2} ${(sy + sleeveEnd) / 2} ${rax - armThick * 0.5} ${sy + 12}
    Z
  `

  return bodyPath + ' ' + lSleeve + ' ' + rSleeve
})

// ── Male board shorts / trunks ────────────────────────────────────
const maleBottomPath = computed(() => {
  const hw = hipW.value / 2
  const ww = waistW.value / 2
  const topY = hipTopY.value - 4
  const legThick = hw * 0.56

  // Hem Y depends on length
  const hemY = {
    trunk: crotchY.value + 20 * heightScale.value,
    'board-above': crotchY.value + 60 * heightScale.value,
    'board-knee': kneeY.value,
    'board-below': kneeY.value + 40 * heightScale.value,
  }[maleSuit.bottom] ?? kneeY.value

  const lx = cx - hw * 0.28
  const rx = cx + hw * 0.28

  // Interpolate leg width at hem
  const legAtHem = (y: number) => {
    const t = (y - crotchY.value) / (legBottom.value - crotchY.value)
    return legThick * (1 - t * 0.3)
  }

  const lw = legAtHem(hemY)
  const rw = legAtHem(hemY)

  return `
    M ${cx - ww * 0.9} ${topY}
    Q ${cx - hw * 1.0} ${topY + (crotchY.value - topY) * 0.4} ${cx - hw * 0.6} ${crotchY.value}
    Q ${lx - lw * 0.3} ${(crotchY.value + hemY) / 2} ${lx - lw * 0.45} ${hemY}
    L ${lx + lw * 0.35} ${hemY}
    Q ${cx - hw * 0.05} ${hemY - 4} ${cx} ${crotchY.value + 8}
    Q ${cx + hw * 0.05} ${hemY - 4} ${rx - rw * 0.35} ${hemY}
    L ${rx + rw * 0.45} ${hemY}
    Q ${rx + rw * 0.3} ${(crotchY.value + hemY) / 2} ${cx + hw * 0.6} ${crotchY.value}
    Q ${cx + hw * 1.0} ${topY + (crotchY.value - topY) * 0.4} ${cx + ww * 0.9} ${topY}
    Q ${cx} ${topY - 6} ${cx - ww * 0.9} ${topY}
    Z
  `
})

// ── Male wetsuit (overrides top + bottom when active) ─────────────
const wetsuitPath = computed(() => {
  if (maleSuit.wetsuit === 'none') return ''

  const sw = shoulderW.value
  const ww = waistW.value / 2
  const hw = hipW.value / 2
  const sy = shoulderY.value
  const armThick = 20 * buildScale.value * 0.9
  const legThick = hw * 0.56

  // Leg coverage
  const legHemY = {
    shorty: crotchY.value + 40 * heightScale.value,
    spring: kneeY.value,
    full: legBottom.value - 20 * heightScale.value,
  }[maleSuit.wetsuit] ?? kneeY.value

  // Arm coverage
  const sleeveEnd = {
    shorty: sy + 40 * heightScale.value,
    spring: sy + 40 * heightScale.value,
    full: waistY.value + 10,
  }[maleSuit.wetsuit] ?? sy + 40 * heightScale.value

  const lx = cx - hw * 0.28
  const rx = cx + hw * 0.28

  const legAtHem = (y: number) => {
    const t = (y - crotchY.value) / (legBottom.value - crotchY.value)
    return legThick * (1 - t * 0.3)
  }
  const lw = legAtHem(legHemY)
  const rw = legAtHem(legHemY)

  // Main body + legs
  const bodyLegs = `
    M ${cx - sw * 1.05} ${sy + 6}
    Q ${cx - sw * 0.5} ${sy - 8} ${cx} ${sy - 6}
    Q ${cx + sw * 0.5} ${sy - 8} ${cx + sw * 1.05} ${sy + 6}
    Q ${cx + ww * 0.8} ${waistY.value} ${cx + hw * 0.6} ${crotchY.value}
    Q ${rx + legThick * 0.3} ${(crotchY.value + legHemY) / 2} ${rx + rw * 0.45} ${legHemY}
    L ${rx - rw * 0.35} ${legHemY}
    Q ${cx + hw * 0.05} ${legHemY - 4} ${cx} ${crotchY.value + 8}
    Q ${cx - hw * 0.05} ${legHemY - 4} ${lx + lw * 0.35} ${legHemY}
    L ${lx - lw * 0.45} ${legHemY}
    Q ${lx - lw * 0.3} ${(crotchY.value + legHemY) / 2} ${cx - hw * 0.6} ${crotchY.value}
    Q ${cx - ww * 0.8} ${waistY.value} ${cx - sw * 1.05} ${sy + 6}
    Z
  `

  const lax = cx - sw
  const rax = cx + sw
  const lSleeve = `
    M ${lax - armThick * 0.6} ${sy + 12}
    Q ${lax - armThick * 0.9} ${(sy + sleeveEnd) / 2} ${lax - armThick * 0.5} ${sleeveEnd}
    L ${lax + armThick * 0.4} ${sleeveEnd}
    Q ${lax + armThick * 0.2} ${(sy + sleeveEnd) / 2} ${lax + armThick * 0.5} ${sy + 12}
    Z
  `
  const rSleeve = `
    M ${rax + armThick * 0.6} ${sy + 12}
    Q ${rax + armThick * 0.9} ${(sy + sleeveEnd) / 2} ${rax + armThick * 0.5} ${sleeveEnd}
    L ${rax - armThick * 0.4} ${sleeveEnd}
    Q ${rax - armThick * 0.2} ${(sy + sleeveEnd) / 2} ${rax - armThick * 0.5} ${sy + 12}
    Z
  `

  return bodyLegs + ' ' + lSleeve + ' ' + rSleeve
})

// ── Labels ────────────────────────────────────────────────────────
const heightLabel = computed(() => {
  const ft = Math.floor(body.height / 12)
  const inch = body.height % 12
  return `${ft}'${inch}"`
})

const buildLabel = computed(() => {
  const labels = ['', 'very lean', 'lean', 'slim', 'athletic', 'average', 'solid', 'stocky', 'full', 'heavy', 'extra heavy']
  return labels[body.build] || ''
})

// ── Defaults per body type ────────────────────────────────────────
function setBodyType(type: BodyType) {
  bodyType.value = type
  if (type === 'male') {
    body.chest = 42
    body.waist = 36
    body.hips = 38
    body.shoulders = 20
    body.build = 5
  } else {
    body.chest = 38
    body.waist = 32
    body.hips = 42
    body.shoulders = 16
    body.build = 5
  }
}
</script>

<template>
  <div class="fitting-room">
    <div class="figure-panel">
      <svg
        :viewBox="`0 0 300 ${svgHeight}`"
        class="body-figure"
        @click="clearZone"
      >
        <defs>
          <linearGradient id="skinGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" :stop-color="skinShadow" />
            <stop offset="40%" :stop-color="skinColor" />
            <stop offset="100%" :stop-color="skinShadow" />
          </linearGradient>
          <linearGradient id="suitTopGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" :stop-color="suitColor" stop-opacity="0.9" />
            <stop offset="100%" :stop-color="suitColorDark" stop-opacity="0.95" />
          </linearGradient>
          <linearGradient id="suitBotGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" :stop-color="suitColor" stop-opacity="0.9" />
            <stop offset="100%" :stop-color="suitColorDark" stop-opacity="0.95" />
          </linearGradient>
          <!-- Wetsuit uses a slightly different material look -->
          <linearGradient id="wetsuitGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" :stop-color="suitColor" stop-opacity="0.85" />
            <stop offset="50%" :stop-color="suitColorDark" stop-opacity="0.9" />
            <stop offset="100%" :stop-color="suitColor" stop-opacity="0.8" />
          </linearGradient>
        </defs>

        <!-- HAIR (behind head for long/medium styles) -->
        <path
          v-if="hairLength !== 'short'"
          :d="hairPath"
          :fill="hairColor"
        />

        <!-- HEAD -->
        <ellipse
          :cx="cx"
          :cy="headY"
          :rx="headW"
          :ry="headH"
          fill="url(#skinGrad)"
        />

        <!-- HAIR (short on top of head) -->
        <path
          v-if="hairLength === 'short'"
          :d="hairPath"
          :fill="hairColor"
        />

        <!-- NECK -->
        <rect
          :x="cx - neckW / 2"
          :y="headY + headH - 4"
          :width="neckW"
          :height="neckH"
          fill="url(#skinGrad)"
        />

        <!-- SHOULDERS + UPPER BODY -->
        <path :d="shoulderPath" fill="url(#skinGrad)" />

        <!-- ARMS -->
        <path :d="leftArmPath" fill="url(#skinGrad)" />
        <path :d="rightArmPath" fill="url(#skinGrad)" />

        <!-- TORSO -->
        <path :d="torsoSkinPath" fill="url(#skinGrad)" />

        <!-- LEGS -->
        <path :d="leftLegPath" fill="url(#skinGrad)" />
        <path :d="rightLegPath" fill="url(#skinGrad)" />

        <!-- FEET -->
        <ellipse :cx="cx - hipW * 0.28" :cy="legBottom + 14" rx="14" ry="8" fill="url(#skinGrad)" />
        <ellipse :cx="cx + hipW * 0.28" :cy="legBottom + 14" rx="14" ry="8" fill="url(#skinGrad)" />

        <!-- ── FEMALE GARMENTS ── -->
        <template v-if="!isMale">
          <path
            :d="suitTopPath"
            fill="url(#suitTopGrad)"
            class="suit-zone"
            :class="{ active: activeZone === 'top' }"
            @click.stop="selectZone('top')"
          />
          <path
            :d="femaleSuitBottomPath"
            fill="url(#suitBotGrad)"
            class="suit-zone"
            :class="{ active: activeZone === 'bottom' }"
            @click.stop="selectZone('bottom')"
          />
        </template>

        <!-- ── MALE GARMENTS ── -->
        <template v-if="isMale">
          <!-- Wetsuit (replaces top + bottom when active) -->
          <template v-if="maleSuit.wetsuit !== 'none'">
            <path
              :d="wetsuitPath"
              fill="url(#wetsuitGrad)"
              class="suit-zone"
              :class="{ active: activeZone === 'wetsuit' }"
              @click.stop="selectZone('wetsuit')"
            />
          </template>
          <template v-else>
            <!-- Rash guard / tank top -->
            <path
              v-if="maleSuit.top !== 'none'"
              :d="maleTopPath"
              fill="url(#suitTopGrad)"
              class="suit-zone"
              :class="{ active: activeZone === 'top' }"
              @click.stop="selectZone('top')"
            />
            <!-- Board shorts / trunks -->
            <path
              :d="maleBottomPath"
              fill="url(#suitBotGrad)"
              class="suit-zone"
              :class="{ active: activeZone === 'bottom' }"
              @click.stop="selectZone('bottom')"
            />
          </template>
        </template>

        <!-- ZONE HIGHLIGHT -->
        <path
          v-if="activeZone === 'top' && !isMale"
          :d="suitTopPath"
          fill="none" stroke="white" stroke-width="2" opacity="0.8"
        />
        <path
          v-if="activeZone === 'bottom' && !isMale"
          :d="femaleSuitBottomPath"
          fill="none" stroke="white" stroke-width="2" opacity="0.8"
        />

        <text :x="cx" :y="shoulderY - 6" text-anchor="middle" class="zone-label">tap garment to adjust</text>
      </svg>
    </div>

    <!-- CONTROLS PANEL -->
    <div class="controls-panel">
      <!-- Body type toggle -->
      <section class="control-section">
        <h3>Body Type</h3>
        <div class="toggle-row">
          <button
            :class="['toggle-btn', { selected: bodyType === 'female' }]"
            @click="setBodyType('female')"
          >Female</button>
          <button
            :class="['toggle-btn', { selected: bodyType === 'male' }]"
            @click="setBodyType('male')"
          >Male</button>
        </div>
      </section>

      <section class="control-section">
        <h3>Body</h3>

        <label>Height <span>{{ heightLabel }}</span></label>
        <input type="range" v-model.number="body.height" min="56" max="82" />

        <label>Build <span>{{ buildLabel }}</span></label>
        <input type="range" v-model.number="body.build" min="1" max="10" />

        <label>Shoulders <span>{{ body.shoulders }}"</span></label>
        <input type="range" v-model.number="body.shoulders" min="14" max="24" />

        <label>{{ isMale ? 'Chest' : 'Bust' }} <span>{{ body.chest }}"</span></label>
        <input type="range" v-model.number="body.chest" min="26" max="58" />

        <label>Waist <span>{{ body.waist }}"</span></label>
        <input type="range" v-model.number="body.waist" min="22" max="58" />

        <label>Hips <span>{{ body.hips }}"</span></label>
        <input type="range" v-model.number="body.hips" min="28" max="64" />
      </section>

      <section class="control-section">
        <h3>Appearance</h3>

        <label>Skin Tone</label>
        <div class="swatch-row">
          <button
            v-for="tone in skinTones"
            :key="tone.color"
            class="swatch"
            :style="{ background: tone.color }"
            :class="{ selected: skinColor === tone.color }"
            @click="skinColor = tone.color; skinShadow = tone.shadow"
          />
        </div>

        <label>Hair Color</label>
        <div class="swatch-row">
          <button
            v-for="h in hairColors"
            :key="h"
            class="swatch"
            :style="{ background: h }"
            :class="{ selected: hairColor === h }"
            @click="hairColor = h"
          />
        </div>

        <label>Hair Length</label>
        <div class="option-row">
          <button
            v-for="len in (['short', 'medium', 'long'] as const)"
            :key="len"
            :class="{ selected: hairLength === len }"
            @click="hairLength = len"
          >{{ len }}</button>
        </div>
      </section>

      <!-- FEMALE SUIT CONTROLS -->
      <section v-if="!isMale" class="control-section">
        <h3>Swimsuit</h3>

        <label>Color</label>
        <div class="swatch-row">
          <button
            v-for="s in suitOptions"
            :key="s.color"
            class="swatch"
            :style="{ background: s.color }"
            :class="{ selected: suitColor === s.color }"
            @click="suitColor = s.color; suitColorDark = s.dark"
          />
        </div>

        <label>Top Style</label>
        <div class="option-row">
          <button
            v-for="style in topStyles"
            :key="style"
            :class="{ selected: femaleSuit.topStyle === style }"
            @click="femaleSuit.topStyle = style"
          >{{ style }}</button>
        </div>

        <label>Bottom Rise</label>
        <div class="option-row">
          <button
            v-for="rise in riseOptions"
            :key="rise"
            :class="{ selected: femaleSuit.rise === rise }"
            @click="femaleSuit.rise = rise"
          >{{ rise }}</button>
        </div>

        <label>Bottom Coverage</label>
        <div class="option-row">
          <button
            v-for="cov in coverageOptions"
            :key="cov"
            :class="{ selected: femaleSuit.coverage === cov }"
            @click="femaleSuit.coverage = cov"
          >{{ cov }}</button>
        </div>
      </section>

      <!-- MALE SUIT CONTROLS -->
      <section v-if="isMale" class="control-section">
        <h3>Swimwear</h3>

        <label>Color</label>
        <div class="swatch-row">
          <button
            v-for="s in suitOptions"
            :key="s.color"
            class="swatch"
            :style="{ background: s.color }"
            :class="{ selected: suitColor === s.color }"
            @click="suitColor = s.color; suitColorDark = s.dark"
          />
        </div>

        <label>Top</label>
        <div class="option-row">
          <button
            v-for="opt in maleTopOptions"
            :key="opt.value"
            :class="{ selected: maleSuit.top === opt.value, disabled: maleSuit.wetsuit !== 'none' }"
            :disabled="maleSuit.wetsuit !== 'none'"
            @click="maleSuit.top = opt.value as typeof maleSuit.top"
          >{{ opt.label }}</button>
        </div>

        <label>Shorts</label>
        <div class="option-row">
          <button
            v-for="opt in maleBottomOptions"
            :key="opt.value"
            :class="{ selected: maleSuit.bottom === opt.value, disabled: maleSuit.wetsuit !== 'none' }"
            :disabled="maleSuit.wetsuit !== 'none'"
            @click="maleSuit.bottom = opt.value as typeof maleSuit.bottom"
          >{{ opt.label }}</button>
        </div>

        <label>Wetsuit</label>
        <div class="option-row">
          <button
            v-for="opt in wetsuitOptions"
            :key="opt.value"
            :class="{ selected: maleSuit.wetsuit === opt.value }"
            @click="maleSuit.wetsuit = opt.value as typeof maleSuit.wetsuit"
          >{{ opt.label }}</button>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.fitting-room {
  display: flex;
  gap: 0;
  height: 100vh;
  background: #0e0e12;
  color: #e8e0d5;
  font-family: system-ui, sans-serif;
}

.figure-panel {
  flex: 0 0 380px;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 24px 16px;
  background: #16161e;
  overflow-y: auto;
}

.body-figure {
  width: 280px;
  filter: drop-shadow(0 8px 32px rgba(0,0,0,0.6));
}

.suit-zone {
  cursor: pointer;
  transition: filter 0.15s;
}

.suit-zone:hover {
  filter: brightness(1.2);
}

.suit-zone.active {
  filter: brightness(1.35);
}

.zone-label {
  font-size: 10px;
  fill: rgba(255,255,255,0.3);
  pointer-events: none;
}

.controls-panel {
  flex: 1;
  overflow-y: auto;
  padding: 24px 28px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.control-section {
  background: #1e1e28;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.control-section h3 {
  margin: 0 0 4px;
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #888;
}

label {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #ccc;
}

label span {
  color: #e8c4a0;
  font-variant-numeric: tabular-nums;
}

input[type='range'] {
  width: 100%;
  accent-color: #7c5cbf;
  cursor: pointer;
  margin-bottom: 4px;
}

/* Body type toggle */
.toggle-row {
  display: flex;
  gap: 0;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #3a3a4a;
}

.toggle-btn {
  flex: 1;
  padding: 8px 0;
  background: #2a2a36;
  color: #999;
  border: none;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.toggle-btn.selected {
  background: #7c5cbf;
  color: white;
}

.toggle-btn:not(.selected):hover {
  background: #3a3a4e;
  color: #ddd;
}

.swatch-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.swatch {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 2px solid transparent;
  cursor: pointer;
  transition: transform 0.1s, border-color 0.1s;
}

.swatch:hover {
  transform: scale(1.15);
}

.swatch.selected {
  border-color: white;
  transform: scale(1.15);
}

.option-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.option-row button {
  background: #2a2a36;
  color: #bbb;
  border: 1px solid #3a3a4a;
  border-radius: 6px;
  padding: 5px 12px;
  font-size: 12px;
  cursor: pointer;
  transition: background 0.12s, color 0.12s;
}

.option-row button:hover:not(:disabled) {
  background: #3a3a4e;
  color: #eee;
}

.option-row button.selected {
  background: #7c5cbf;
  color: white;
  border-color: #7c5cbf;
}

.option-row button:disabled,
.option-row button.disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

@media (max-width: 720px) {
  .fitting-room {
    flex-direction: column;
    height: auto;
    min-height: 100vh;
  }

  .figure-panel {
    flex: none;
    height: 50vh;
    min-height: 320px;
  }
}
</style>
