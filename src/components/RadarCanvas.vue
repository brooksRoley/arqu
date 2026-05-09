<template>
  <div ref="wrapRef" class="radar-wrap">
    <canvas ref="baseRef" class="radar-canvas radar-base" />
    <canvas ref="overlayRef" class="radar-canvas radar-overlay" />
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

interface BigFiveScores { O: number; C: number; E: number; A: number; N: number }

const props = withDefaults(defineProps<{
  scores?: BigFiveScores
  size?: number
  color?: string
}>(), {
  scores: () => ({ O: 72, C: 58, E: 45, A: 81, N: 63 }),
  size: 320,
  color: '#a3e635',
})

const wrapRef = ref<HTMLDivElement>()
const baseRef = ref<HTMLCanvasElement>()
const overlayRef = ref<HTMLCanvasElement>()

const AXES: Array<{ key: keyof BigFiveScores; label: string }> = [
  { key: 'O', label: 'Openness' },
  { key: 'C', label: 'Conscientiousness' },
  { key: 'E', label: 'Extraversion' },
  { key: 'A', label: 'Agreeableness' },
  { key: 'N', label: 'Neuroticism' },
]

let raf = 0
let t0 = 0
let dpr = 1
let mounted = false

function fit(canvas: HTMLCanvasElement, size: number) {
  dpr = Math.min(window.devicePixelRatio || 1, 2)
  canvas.width = size * dpr
  canvas.height = size * dpr
  canvas.style.width = `${size}px`
  canvas.style.height = `${size}px`
  const ctx = canvas.getContext('2d')!
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  return ctx
}

function axisPoint(cx: number, cy: number, radius: number, i: number, n: number) {
  const angle = -Math.PI / 2 + (i * 2 * Math.PI) / n
  return { x: cx + Math.cos(angle) * radius, y: cy + Math.sin(angle) * radius, angle }
}

function drawBase(ctx: CanvasRenderingContext2D, size: number) {
  const cx = size / 2
  const cy = size / 2
  const maxR = size * 0.36

  ctx.clearRect(0, 0, size, size)

  // Concentric pentagon rings
  for (let ring = 1; ring <= 4; ring++) {
    const r = (maxR * ring) / 4
    ctx.beginPath()
    for (let i = 0; i < AXES.length; i++) {
      const p = axisPoint(cx, cy, r, i, AXES.length)
      if (i === 0) ctx.moveTo(p.x, p.y)
      else ctx.lineTo(p.x, p.y)
    }
    ctx.closePath()
    ctx.strokeStyle = `rgba(163, 230, 53, ${0.05 + ring * 0.025})`
    ctx.lineWidth = 1
    ctx.stroke()
  }

  // Spokes
  for (let i = 0; i < AXES.length; i++) {
    const p = axisPoint(cx, cy, maxR, i, AXES.length)
    ctx.beginPath()
    ctx.moveTo(cx, cy)
    ctx.lineTo(p.x, p.y)
    ctx.strokeStyle = 'rgba(163, 230, 53, 0.12)'
    ctx.lineWidth = 1
    ctx.stroke()
  }
}

function drawOverlay(ctx: CanvasRenderingContext2D, size: number, t: number, intro: number) {
  const cx = size / 2
  const cy = size / 2
  const maxR = size * 0.36

  ctx.clearRect(0, 0, size, size)

  const pulse = 0.92 + Math.sin(t * 0.0018) * 0.05
  const eased = intro * intro * (3 - 2 * intro)

  // Filled scores polygon
  ctx.beginPath()
  for (let i = 0; i < AXES.length; i++) {
    const score = props.scores[AXES[i].key] ?? 0
    const r = maxR * (score / 100) * eased * pulse
    const p = axisPoint(cx, cy, r, i, AXES.length)
    if (i === 0) ctx.moveTo(p.x, p.y)
    else ctx.lineTo(p.x, p.y)
  }
  ctx.closePath()

  const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, maxR)
  grad.addColorStop(0, 'rgba(163, 230, 53, 0.32)')
  grad.addColorStop(1, 'rgba(163, 230, 53, 0.10)')
  ctx.fillStyle = grad
  ctx.fill()
  ctx.strokeStyle = props.color
  ctx.lineWidth = 1.5
  ctx.shadowColor = props.color
  ctx.shadowBlur = 12 * pulse
  ctx.stroke()
  ctx.shadowBlur = 0

  // Score nodes
  for (let i = 0; i < AXES.length; i++) {
    const score = props.scores[AXES[i].key] ?? 0
    const r = maxR * (score / 100) * eased * pulse
    const p = axisPoint(cx, cy, r, i, AXES.length)
    ctx.beginPath()
    ctx.arc(p.x, p.y, 3, 0, Math.PI * 2)
    ctx.fillStyle = props.color
    ctx.fill()
  }

  // Axis labels (rendered on overlay so they sit above the polygon glow)
  ctx.font = '10px ui-monospace, SFMono-Regular, Menlo, monospace'
  ctx.fillStyle = 'rgba(163, 230, 53, 0.85)'
  ctx.textBaseline = 'middle'
  for (let i = 0; i < AXES.length; i++) {
    const labelP = axisPoint(cx, cy, maxR + 18, i, AXES.length)
    const score = props.scores[AXES[i].key] ?? 0
    const isTop = i === 0
    const isLeft = labelP.x < cx - 1
    const isRight = labelP.x > cx + 1
    ctx.textAlign = isTop ? 'center' : isRight ? 'left' : isLeft ? 'right' : 'center'
    const letter = AXES[i].key
    ctx.fillStyle = props.color
    ctx.fillText(letter, labelP.x, labelP.y - 6)
    ctx.fillStyle = 'rgba(163, 230, 53, 0.55)'
    ctx.fillText(`${Math.round(score)}`, labelP.x, labelP.y + 6)
  }
}

function loop(now: number) {
  if (!mounted || !overlayRef.value) return
  if (!t0) t0 = now
  const elapsed = now - t0
  const intro = Math.min(1, elapsed / 900)
  const ctx = overlayRef.value.getContext('2d')!
  drawOverlay(ctx, props.size, elapsed, intro)
  raf = requestAnimationFrame(loop)
}

function rebuild() {
  if (!baseRef.value || !overlayRef.value) return
  const baseCtx = fit(baseRef.value, props.size)
  fit(overlayRef.value, props.size)
  drawBase(baseCtx, props.size)
  t0 = 0
}

onMounted(() => {
  mounted = true
  rebuild()
  raf = requestAnimationFrame(loop)
})

onBeforeUnmount(() => {
  mounted = false
  cancelAnimationFrame(raf)
})

watch(() => [props.size, props.scores], () => rebuild(), { deep: true })
</script>

<style scoped>
.radar-wrap {
  position: relative;
  display: inline-block;
  line-height: 0;
}
.radar-canvas {
  display: block;
}
.radar-base {
  position: relative;
}
.radar-overlay {
  position: absolute;
  inset: 0;
  pointer-events: none;
}
</style>
