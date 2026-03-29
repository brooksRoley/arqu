import { ref, onMounted, onUnmounted, type Ref } from 'vue'

export interface AnimationContext {
  ctx: CanvasRenderingContext2D
  width: number
  height: number
  /** Elapsed time in seconds since animation start */
  time: number
  /** Delta time in seconds since last frame */
  dt: number
}

export interface UseAnimationCanvasOptions {
  /** Main draw callback — called every frame after the background layer */
  draw: (ac: AnimationContext) => void
  /** Whether to draw the plasma/snow background (default true) */
  plasmaBackground?: boolean
  /** Background base color [r, g, b] — default [10, 10, 20] */
  bgColor?: [number, number, number]
  /** Plasma intensity 0–1 (default 0.4) */
  plasmaIntensity?: number
  /** Snow particle count (default 120) */
  snowCount?: number
}

/**
 * Composable that manages a fullscreen canvas with:
 * - Automatic resize + DPR scaling
 * - Smooth RAF loop with time/dt
 * - Optional plasma + snow background layer
 *
 * Usage:
 *   const canvasRef = ref<HTMLCanvasElement>()
 *   useAnimationCanvas(canvasRef, { draw(ac) { ... } })
 */
export function useAnimationCanvas(
  canvasRef: Ref<HTMLCanvasElement | undefined>,
  options: UseAnimationCanvasOptions
) {
  const {
    draw,
    plasmaBackground = true,
    bgColor = [10, 10, 20],
    plasmaIntensity = 0.4,
    snowCount = 120
  } = options

  const isRunning = ref(false)
  let rafId = 0
  let startTime = 0
  let lastTime = 0
  let width = 0
  let height = 0
  let dpr = 1

  // Snow particles — seeded once
  interface Snowflake {
    x: number
    y: number
    vx: number
    vy: number
    size: number
    opacity: number
    wobblePhase: number
    wobbleSpeed: number
  }

  let snowflakes: Snowflake[] = []

  function initSnow() {
    snowflakes = Array.from({ length: snowCount }, () => ({
      x: Math.random(),
      y: Math.random(),
      vx: (Math.random() - 0.5) * 0.015,
      vy: 0.008 + Math.random() * 0.02,
      size: 1 + Math.random() * 2.5,
      opacity: 0.15 + Math.random() * 0.45,
      wobblePhase: Math.random() * Math.PI * 2,
      wobbleSpeed: 0.3 + Math.random() * 0.8
    }))
  }

  function resize() {
    const canvas = canvasRef.value
    if (!canvas) return
    dpr = Math.min(window.devicePixelRatio || 1, 2)
    width = canvas.clientWidth
    height = canvas.clientHeight
    canvas.width = width * dpr
    canvas.height = height * dpr
    const ctx = canvas.getContext('2d')!
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  }

  // ── Plasma background layer ──────────────────────────────────────
  function drawPlasma(ctx: CanvasRenderingContext2D, t: number) {
    // Soft full-screen clear with slight trail
    ctx.fillStyle = `rgba(${bgColor[0]}, ${bgColor[1]}, ${bgColor[2]}, 0.92)`
    ctx.fillRect(0, 0, width, height)

    const cx = width / 2
    const cy = height / 2
    const maxR = Math.hypot(cx, cy)
    const intensity = plasmaIntensity

    // Plasma blobs — 4 overlapping radial gradients that drift
    const blobs = [
      { angle: t * 0.13, dist: 0.25, r: 0.35, color: [80, 60, 160] },
      { angle: t * 0.09 + 2, dist: 0.3, r: 0.3, color: [40, 100, 180] },
      { angle: t * 0.11 + 4, dist: 0.2, r: 0.4, color: [100, 40, 140] },
      { angle: t * 0.07 + 1, dist: 0.35, r: 0.25, color: [60, 80, 200] }
    ]

    for (const blob of blobs) {
      const bx = cx + Math.cos(blob.angle) * maxR * blob.dist
      const by = cy + Math.sin(blob.angle) * maxR * blob.dist
      const br = maxR * blob.r * (0.8 + 0.2 * Math.sin(t * 0.5 + blob.angle))

      const grad = ctx.createRadialGradient(bx, by, 0, bx, by, br)
      const [r, g, b] = blob.color
      const a = intensity * 0.12
      grad.addColorStop(0, `rgba(${r}, ${g}, ${b}, ${a})`)
      grad.addColorStop(0.6, `rgba(${r}, ${g}, ${b}, ${a * 0.4})`)
      grad.addColorStop(1, `rgba(${r}, ${g}, ${b}, 0)`)

      ctx.fillStyle = grad
      ctx.fillRect(0, 0, width, height)
    }
  }

  // ── Snow layer ───────────────────────────────────────────────────
  function drawSnow(ctx: CanvasRenderingContext2D, t: number, dt: number) {
    for (const s of snowflakes) {
      // Wobble horizontally
      s.x += s.vx * dt + Math.sin(t * s.wobbleSpeed + s.wobblePhase) * 0.0008
      s.y += s.vy * dt

      // Wrap
      if (s.y > 1.02) { s.y = -0.02; s.x = Math.random() }
      if (s.x < -0.02) s.x = 1.02
      if (s.x > 1.02) s.x = -0.02

      const px = s.x * width
      const py = s.y * height

      // Glow
      const glowR = s.size * 3
      const grad = ctx.createRadialGradient(px, py, 0, px, py, glowR)
      grad.addColorStop(0, `rgba(200, 210, 255, ${s.opacity * 0.5})`)
      grad.addColorStop(1, 'rgba(200, 210, 255, 0)')
      ctx.fillStyle = grad
      ctx.fillRect(px - glowR, py - glowR, glowR * 2, glowR * 2)

      // Core
      ctx.beginPath()
      ctx.arc(px, py, s.size, 0, Math.PI * 2)
      ctx.fillStyle = `rgba(220, 225, 255, ${s.opacity})`
      ctx.fill()
    }
  }

  // ── Main loop ────────────────────────────────────────────────────
  function loop(timestamp: number) {
    if (!isRunning.value) return
    const canvas = canvasRef.value
    if (!canvas) { rafId = requestAnimationFrame(loop); return }

    const ctx = canvas.getContext('2d')!
    if (!startTime) { startTime = timestamp; lastTime = timestamp }
    const time = (timestamp - startTime) / 1000
    const dt = Math.min((timestamp - lastTime) / 1000, 0.1) // cap to avoid jumps
    lastTime = timestamp

    if (plasmaBackground) {
      drawPlasma(ctx, time)
      drawSnow(ctx, time, dt)
    }

    draw({ ctx, width, height, time, dt })

    rafId = requestAnimationFrame(loop)
  }

  function start() {
    if (isRunning.value) return
    isRunning.value = true
    startTime = 0
    lastTime = 0
    rafId = requestAnimationFrame(loop)
  }

  function stop() {
    isRunning.value = false
    if (rafId) cancelAnimationFrame(rafId)
    rafId = 0
  }

  onMounted(() => {
    initSnow()
    resize()
    window.addEventListener('resize', resize)
    start()
  })

  onUnmounted(() => {
    stop()
    window.removeEventListener('resize', resize)
  })

  return { isRunning, start, stop, resize }
}
