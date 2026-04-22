import { ref, reactive, type Ref } from 'vue'
import Matter from 'matter-js'

// ── Default orb palette ───────────────────────────────────────────
export const DEFAULT_ORB_DEFS = [
  { r: 123, g: 94,  b: 167 },  // purple
  { r: 58,  g: 107, b: 138 },  // teal
  { r: 138, g: 122, b: 90  },  // amber
  { r: 90,  g: 138, b: 107 },  // green
  { r: 99,  g: 102, b: 241 },  // indigo
  { r: 160, g: 90,  b: 123 },  // rose
]

// ── Types ─────────────────────────────────────────────────────────
export interface OrbDef { r: number; g: number; b: number }

export interface Particle {
  x: number; y: number; vx: number; vy: number
  size: number; alpha: number; depth: number
  nearOrb: number; orbDist: number
}
export interface Star {
  x: number; y: number; size: number; bright: number
  twSpd: number; twOff: number; depth: number
}
export interface Orb {
  body: any; color: OrbDef; radius: number
  heat: number; glowR: number; pulse: number
  springTarget: { x: number; y: number } | null
  springHome: { x: number; y: number }
}

export interface CosmicConfig {
  orbDefs?: OrbDef[]
  particleCount?: number
  starCount?: number
  enableKeyboard?: boolean
  enableMouseInteract?: boolean
  /** Opacity of the trail fade — higher = more opaque = faster fade. 0.11 = immersive, 0.06 = softer bg */
  clearAlpha?: number
  /** Multiplier for mouse-to-orb attraction force. 0 = no attraction */
  mouseAttractForce?: number
}

const DEFAULTS: Required<CosmicConfig> = {
  orbDefs: DEFAULT_ORB_DEFS,
  particleCount: 220,
  starCount: 160,
  enableKeyboard: true,
  enableMouseInteract: true,
  clearAlpha: 0.11,
  mouseAttractForce: 1,
}

export function useCosmicPhysics(canvasRef: Ref<HTMLCanvasElement | undefined>, userConfig: CosmicConfig = {}) {
  const cfg = { ...DEFAULTS, ...userConfig }

  // ── Reactive state ──────────────────────────────────────────────
  const loaded = ref(false)
  const adapt = reactive({ focus: 0, engage: 0, depth: 0, mVel: 0 })

  // ── Non-reactive internals ──────────────────────────────────────
  const M = Matter
  let engine: any = null
  let ctx: CanvasRenderingContext2D
  let W = 0, H = 0, dpr = 1
  let raf = 0, t0 = 0, tPrev = 0
  let orbs: Orb[] = []
  let particles: Particle[] = []
  let stars: Star[] = []
  let pxSmooth = { x: 0, y: 0 }
  let pxTarget = { x: 0, y: 0 }
  let lastMx = 0, lastMy = 0, lastMoveT = 0

  // Keyboard
  const keysDown = new Set<string>()
  let selectedOrb = 0
  const KEY_FORCE = 6e-3

  // Card attractors (DOM-space positions acting as gravity wells)
  let cardAttractors: { x: number; y: number; mass: number }[] = []

  // ── Init helpers ────────────────────────────────────────────────
  function initStars() {
    stars = Array.from({ length: cfg.starCount }, () => ({
      x: Math.random(), y: Math.random(),
      size: 0.4 + Math.random() * 1.4,
      bright: 0.15 + Math.random() * 0.45,
      twSpd: 0.4 + Math.random() * 2.2,
      twOff: Math.random() * Math.PI * 2,
      depth: 0.03 + Math.random() * 0.12,
    }))
  }

  function initParticles() {
    particles = Array.from({ length: cfg.particleCount }, () => ({
      x: Math.random() * W, y: Math.random() * H,
      vx: (Math.random() - 0.5) * 0.3,
      vy: (Math.random() - 0.5) * 0.3,
      size: 0.6 + Math.random() * 2.8,
      alpha: 0.08 + Math.random() * 0.32,
      depth: 0.25 + Math.random() * 0.55,
      nearOrb: 0, orbDist: 1e9,
    }))
  }

  function initPhysics() {
    const { Engine, Bodies, Body, Composite } = M
    engine = Engine.create({ gravity: { x: 0, y: 0 } })

    const cx = W / 2, cy = H / 2
    const spread = Math.min(W, H) * 0.22

    orbs = cfg.orbDefs.map((color, i) => {
      const a = (i / cfg.orbDefs.length) * Math.PI * 2
      const r = 18 + Math.random() * 16
      const body = Bodies.circle(
        cx + Math.cos(a) * spread * (0.6 + Math.random() * 0.4),
        cy + Math.sin(a) * spread * (0.6 + Math.random() * 0.4),
        r, { restitution: 0.5, friction: 0, frictionAir: 0.015, collisionFilter: { group: -1 } }
      )
      Body.setVelocity(body, { x: (Math.random() - 0.5) * 1.2, y: (Math.random() - 0.5) * 1.2 })
      Composite.add(engine.world, body)
      return { body, color, radius: r, heat: 0, glowR: r * 3, pulse: Math.random() * Math.PI * 2, springTarget: null, springHome: { x: cx, y: cy } }
    })

    // Invisible boundary walls
    const p = 100
    Composite.add(engine.world, [
      Bodies.rectangle(W / 2, -p / 2, W + p * 2, p, { isStatic: true }),
      Bodies.rectangle(W / 2, H + p / 2, W + p * 2, p, { isStatic: true }),
      Bodies.rectangle(-p / 2, H / 2, p, H + p * 2, { isStatic: true }),
      Bodies.rectangle(W + p / 2, H / 2, p, H + p * 2, { isStatic: true }),
    ])
  }

  // ── Physics step ────────────────────────────────────────────────
  function stepForces() {
    const { Body } = M
    const cx = W / 2, cy = H / 2
    const centerMul = 1 + adapt.focus * 2

    for (let i = 0; i < orbs.length; i++) {
      const o = orbs[i], p = o.body.position

      // ── Resolve natural home (nearest card or screen center) ──
      let homeX = cx, homeY = cy
      if (cardAttractors.length > 0) {
        let caDist = 1e9
        for (const ca of cardAttractors) {
          const d = Math.hypot(ca.x - p.x, ca.y - p.y) / ca.mass
          if (d < caDist) { caDist = d * ca.mass; homeX = ca.x; homeY = ca.y }
        }
        const cdf = Math.max(Math.hypot(homeX - p.x, homeY - p.y), 1)
        Body.applyForce(o.body, p, {
          x: (homeX - p.x) / cdf * 6e-5 * centerMul,
          y: (homeY - p.y) / cdf * 6e-5 * centerMul,
        })
        const cAng = Math.atan2(p.y - homeY, p.x - homeX) + Math.PI / 2
        Body.applyForce(o.body, p, { x: Math.cos(cAng) * 3e-5, y: Math.sin(cAng) * 3e-5 })
      } else {
        Body.applyForce(o.body, p, {
          x: (cx - p.x) * 3e-5 * centerMul,
          y: (cy - p.y) * 3e-5 * centerMul,
        })
        const ang = Math.atan2(p.y - cy, p.x - cx) + Math.PI / 2
        const orbitF = 2e-5 * (1 - adapt.focus * 0.5)
        Body.applyForce(o.body, p, { x: Math.cos(ang) * orbitF, y: Math.sin(ang) * orbitF })
      }
      o.springHome.x = homeX; o.springHome.y = homeY

      // ── Spring oscillation (from click) ──
      if (o.springTarget) {
        const stx = o.springTarget.x, sty = o.springTarget.y
        // Pull strongly toward spring target
        Body.applyForce(o.body, p, {
          x: (stx - p.x) * 5e-4,
          y: (sty - p.y) * 5e-4,
        })
        // Decay spring target back toward home
        o.springTarget.x += (homeX - stx) * 0.006
        o.springTarget.y += (homeY - sty) * 0.006
        if (Math.hypot(o.springTarget.x - homeX, o.springTarget.y - homeY) < 4) {
          o.springTarget = null
          o.body.frictionAir = 0.015
        }
      }

      // ── Orb–orb repulsion ──
      for (let j = i + 1; j < orbs.length; j++) {
        const q = orbs[j].body.position
        const dx = p.x - q.x, dy = p.y - q.y
        const d = Math.hypot(dx, dy)
        if (d < 160 && d > 1) {
          const f = 6e-5 / d
          Body.applyForce(o.body, p, { x: dx / d * f, y: dy / d * f })
          Body.applyForce(orbs[j].body, q, { x: -dx / d * f, y: -dy / d * f })
        }
      }

      // ── Breathing pulse ──
      o.pulse += 0.006 + adapt.depth * 0.003
      const wave = Math.sin(o.pulse) * 0.5 + 0.5
      o.glowR = o.radius * (2.5 + wave * 1.5 + o.heat * 2)
      o.heat *= 0.96
    }
  }

  // ── Particle step ───────────────────────────────────────────────
  function stepParticles(dt: number) {
    const attr = 0.25 + adapt.focus * 0.35
    const damp = 0.987
    const dt60 = dt * 60

    for (const p of particles) {
      // Always track nearest orb for color/connections
      let mind = 1e9, mi = 0
      for (let i = 0; i < orbs.length; i++) {
        const op = orbs[i].body.position
        const d = Math.hypot(op.x - p.x, op.y - p.y)
        if (d < mind) { mind = d; mi = i }
      }
      p.nearOrb = mi; p.orbDist = mind

      // Physics attraction: prefer card attractors when available
      let attrX: number, attrY: number, attrDist: number
      if (cardAttractors.length > 0) {
        let best = 1e9
        attrX = W / 2; attrY = H / 2; attrDist = 1e9
        for (const ca of cardAttractors) {
          const d = Math.hypot(ca.x - p.x, ca.y - p.y) / ca.mass
          if (d < best) { best = d; attrX = ca.x; attrY = ca.y; attrDist = d * ca.mass }
        }
      } else {
        const op = orbs[mi].body.position
        attrX = op.x; attrY = op.y; attrDist = mind
      }

      if (attrDist > 8) {
        const dx = attrX - p.x, dy = attrY - p.y
        const f = attr / Math.max(attrDist, 40) * dt60
        p.vx += (dx / attrDist) * f
        p.vy += (dy / attrDist) * f
      }

      const swirlRadius = cardAttractors.length > 0 ? 380 : 200
      const swirlStr = cardAttractors.length > 0 ? 0.14 : 0.12
      if (attrDist < swirlRadius && attrDist > 8) {
        const dx = attrX - p.x, dy = attrY - p.y
        const s = swirlStr * (1 - attrDist / swirlRadius) * dt60
        p.vx += (-dy / attrDist) * s
        p.vy += (dx / attrDist) * s
      }

      p.vx += (Math.random() - 0.5) * 0.015
      p.vy += (Math.random() - 0.5) * 0.015
      p.vx *= damp; p.vy *= damp
      const spd = Math.hypot(p.vx, p.vy)
      if (spd > 2.5) { p.vx *= 2.5 / spd; p.vy *= 2.5 / spd }

      p.x += p.vx; p.y += p.vy
      if (p.x < -10) p.x = W + 10; if (p.x > W + 10) p.x = -10
      if (p.y < -10) p.y = H + 10; if (p.y > H + 10) p.y = -10
    }
  }

  // ── Adaptive state ──────────────────────────────────────────────
  function stepAdapt(dt: number) {
    adapt.mVel *= Math.exp(-dt * 2.5)
    adapt.focus += (Math.max(0, 1 - adapt.mVel / 4) - adapt.focus) * dt * 0.4
    adapt.depth = Math.min(1, adapt.depth + dt * 0.005)
    adapt.engage += (Math.min(1, adapt.mVel / 3) - adapt.engage) * dt * 1.8
  }

  // ── Draw layers ─────────────────────────────────────────────────
  function drawClear() {
    ctx.fillStyle = `rgba(8,6,14,${cfg.clearAlpha + adapt.focus * 0.04})`
    ctx.fillRect(0, 0, W, H)
  }

  function drawNebula(t: number) {
    const ox = pxSmooth.x * 0.02, oy = pxSmooth.y * 0.02
    const blobs: [number, number, number, number, number, number][] = [
      [0.3, 0.35, 0.38, 35, 18, 75],
      [0.72, 0.28, 0.32, 18, 38, 68],
      [0.48, 0.72, 0.26, 48, 18, 50],
      [0.18, 0.58, 0.22, 22, 32, 58],
    ]
    for (const [bx, by, br, cr, cg, cb] of blobs) {
      const x = bx * W + ox + Math.sin(t * 0.04 + bx * 9) * 25
      const y = by * H + oy + Math.cos(t * 0.035 + by * 9) * 20
      const rad = br * Math.min(W, H) * (0.85 + 0.15 * Math.sin(t * 0.025 + bx))
      const a = 0.055 + adapt.depth * 0.025
      const g = ctx.createRadialGradient(x, y, 0, x, y, rad)
      g.addColorStop(0, `rgba(${cr},${cg},${cb},${a})`)
      g.addColorStop(0.5, `rgba(${cr},${cg},${cb},${a * 0.3})`)
      g.addColorStop(1, `rgba(${cr},${cg},${cb},0)`)
      ctx.fillStyle = g
      ctx.fillRect(0, 0, W, H)
    }
  }

  function drawStarfield(t: number) {
    const ox = pxSmooth.x * 0.05, oy = pxSmooth.y * 0.05
    for (const s of stars) {
      const x = s.x * W + ox * s.depth * 10
      const y = s.y * H + oy * s.depth * 10
      const tw = Math.sin(t * s.twSpd + s.twOff) * 0.5 + 0.5
      ctx.beginPath()
      ctx.arc(x, y, s.size, 0, Math.PI * 2)
      ctx.fillStyle = `rgba(195,205,235,${s.bright * (0.45 + tw * 0.55)})`
      ctx.fill()
    }
  }

  function drawParticles() {
    const ox = pxSmooth.x * 0.08, oy = pxSmooth.y * 0.08
    for (const p of particles) {
      const x = p.x + ox * p.depth, y = p.y + oy * p.depth
      const c = cfg.orbDefs[p.nearOrb]
      const prox = Math.max(0, 1 - p.orbDist / 300)

      const r = 170 + (c.r - 170) * prox
      const g = 180 + (c.g - 180) * prox
      const b = 215 + (c.b - 215) * prox
      const a = p.alpha * (0.4 + prox * 0.6)

      if (prox > 0.5 && p.size > 1.5 && a > 0.08) {
        const gr = p.size * 5
        const gg = ctx.createRadialGradient(x, y, 0, x, y, gr)
        gg.addColorStop(0, `rgba(${r | 0},${g | 0},${b | 0},${a * 0.25})`)
        gg.addColorStop(1, `rgba(${r | 0},${g | 0},${b | 0},0)`)
        ctx.fillStyle = gg
        ctx.fillRect(x - gr, y - gr, gr * 2, gr * 2)
      }

      ctx.beginPath()
      ctx.arc(x, y, p.size * (0.75 + prox * 0.4), 0, Math.PI * 2)
      ctx.fillStyle = `rgba(${r | 0},${g | 0},${b | 0},${a})`
      ctx.fill()
    }
  }

  function drawConnections() {
    const ox = pxSmooth.x * 0.1, oy = pxSmooth.y * 0.1
    const focusMul = 0.5 + adapt.focus * 0.5
    for (const p of particles) {
      if (p.orbDist > 100) continue
      const o = orbs[p.nearOrb], c = o.color
      const op = o.body.position
      const a = 0.035 * (1 - p.orbDist / 100) * focusMul
      ctx.beginPath()
      ctx.moveTo(p.x + ox * p.depth, p.y + oy * p.depth)
      ctx.lineTo(op.x + ox, op.y + oy)
      ctx.strokeStyle = `rgba(${c.r},${c.g},${c.b},${a})`
      ctx.lineWidth = 0.4
      ctx.stroke()
    }
  }

  function drawOrbs() {
    const ox = pxSmooth.x * 0.12, oy = pxSmooth.y * 0.12
    for (let i = 0; i < orbs.length; i++) {
      const o = orbs[i], p = o.body.position, c = o.color
      const x = p.x + ox, y = p.y + oy

      // Outer glow
      const gg = ctx.createRadialGradient(x, y, 0, x, y, o.glowR)
      gg.addColorStop(0, `rgba(${c.r},${c.g},${c.b},${0.12 + o.heat * 0.12})`)
      gg.addColorStop(0.35, `rgba(${c.r},${c.g},${c.b},${0.04 + o.heat * 0.04})`)
      gg.addColorStop(1, `rgba(${c.r},${c.g},${c.b},0)`)
      ctx.fillStyle = gg
      ctx.beginPath(); ctx.arc(x, y, o.glowR, 0, Math.PI * 2); ctx.fill()

      // Bright core
      const cg = ctx.createRadialGradient(x, y, 0, x, y, o.radius)
      const br = Math.min(255, c.r + 55), bg = Math.min(255, c.g + 55), bb = Math.min(255, c.b + 55)
      cg.addColorStop(0, `rgba(${br},${bg},${bb},${0.55 + o.heat * 0.3})`)
      cg.addColorStop(0.75, `rgba(${c.r},${c.g},${c.b},${0.25 + o.heat * 0.15})`)
      cg.addColorStop(1, `rgba(${c.r},${c.g},${c.b},0.04)`)
      ctx.fillStyle = cg
      ctx.beginPath(); ctx.arc(x, y, o.radius, 0, Math.PI * 2); ctx.fill()

      // Selection ring
      if (cfg.enableKeyboard && i === selectedOrb) {
        ctx.beginPath()
        ctx.arc(x, y, o.radius + 6, 0, Math.PI * 2)
        ctx.strokeStyle = `rgba(${c.r},${c.g},${c.b},${0.25 + Math.sin(Date.now() * 0.004) * 0.15})`
        ctx.lineWidth = 1.5
        ctx.setLineDash([4, 4])
        ctx.stroke()
        ctx.setLineDash([])
      }
    }
  }

  function drawCursor() {
    if (adapt.mVel < 0.01) return
    const intensity = Math.min(1, adapt.mVel * 0.8)
    const r = 25 + adapt.mVel * 18
    const g = ctx.createRadialGradient(lastMx, lastMy, 0, lastMx, lastMy, r)
    g.addColorStop(0, `rgba(160,140,220,${0.06 * intensity})`)
    g.addColorStop(1, 'rgba(160,140,220,0)')
    ctx.fillStyle = g
    ctx.beginPath(); ctx.arc(lastMx, lastMy, r, 0, Math.PI * 2); ctx.fill()
  }

  function drawVignette() {
    const g = ctx.createRadialGradient(
      W / 2, H / 2, Math.min(W, H) * 0.22,
      W / 2, H / 2, Math.max(W, H) * 0.62
    )
    g.addColorStop(0, 'rgba(8,6,14,0)')
    g.addColorStop(1, `rgba(8,6,14,${0.45 + adapt.depth * 0.2})`)
    ctx.fillStyle = g
    ctx.fillRect(0, 0, W, H)
  }

  // ── Input ───────────────────────────────────────────────────────
  function onMove(cx: number, cy: number) {
    const now = performance.now()
    const dx = cx - lastMx, dy = cy - lastMy
    const dtm = Math.max(1, now - lastMoveT)
    adapt.mVel = Math.sqrt(dx * dx + dy * dy) / dtm * 16
    lastMx = cx; lastMy = cy; lastMoveT = now
    pxTarget.x = (cx / (W || 1) - 0.5) * 80
    pxTarget.y = (cy / (H || 1) - 0.5) * 80

    if (!M || !cfg.enableMouseInteract || cfg.mouseAttractForce === 0) return
    const { Body } = M
    for (const o of orbs) {
      const p = o.body.position
      const d = Math.hypot(p.x - cx, p.y - cy)
      if (d < 220 && d > 1) {
        o.heat = Math.min(1, o.heat + 0.04 * (1 - d / 220))
        const f = 8e-5 * (1 - d / 220) * cfg.mouseAttractForce
        Body.applyForce(o.body, p, { x: (cx - p.x) / d * f, y: (cy - p.y) / d * f })
      }
    }
  }

  const _onMouse = (e: MouseEvent) => onMove(e.clientX, e.clientY)
  const _onTouch = (e: TouchEvent) => { const t = e.touches[0]; if (t) onMove(t.clientX, t.clientY) }
  const _onOrient = (e: DeviceOrientationEvent) => {
    pxTarget.x = ((e.gamma ?? 0) / 40) * 60
    pxTarget.y = (((e.beta ?? 45) - 45) / 40) * 60
  }

  // ── Keyboard ────────────────────────────────────────────────────
  function _onKeyDown(e: KeyboardEvent) {
    const tag = (e.target as HTMLElement)?.tagName
    if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return
    if (e.key === 'Tab') {
      e.preventDefault()
      selectedOrb = (selectedOrb + (e.shiftKey ? orbs.length - 1 : 1)) % orbs.length
      if (orbs[selectedOrb]) orbs[selectedOrb].heat = Math.min(1, orbs[selectedOrb].heat + 0.4)
      return
    }
    keysDown.add(e.key)
  }

  function _onKeyUp(e: KeyboardEvent) { keysDown.delete(e.key) }

  function stepKeyboard() {
    if (!M || !orbs.length || keysDown.size === 0) return
    const { Body } = M
    const o = orbs[selectedOrb]
    if (!o) return
    const p = o.body.position
    let fx = 0, fy = 0
    if (keysDown.has('ArrowLeft') || keysDown.has('a') || keysDown.has('A')) fx -= 1
    if (keysDown.has('ArrowRight') || keysDown.has('d') || keysDown.has('D')) fx += 1
    if (keysDown.has('ArrowUp') || keysDown.has('w') || keysDown.has('W')) fy -= 1
    if (keysDown.has('ArrowDown') || keysDown.has('s') || keysDown.has('S')) fy += 1
    if (fx === 0 && fy === 0) return
    const len = Math.hypot(fx, fy)
    fx = (fx / len) * KEY_FORCE; fy = (fy / len) * KEY_FORCE
    Body.applyForce(o.body, p, { x: fx, y: fy })
    o.heat = Math.min(1, o.heat + 0.02)
    // Suppress centering force while keys are held so orbs can escape center gravity
    adapt.mVel = Math.max(adapt.mVel, 3)
  }

  /** Lunge all orbs toward (x, y) and set a spring target so they oscillate back */
  function clickImpulse(x: number, y: number) {
    if (!M || !orbs.length) return
    const { Body } = M
    for (const o of orbs) {
      const p = o.body.position
      const dx = x - p.x, dy = y - p.y
      const d = Math.hypot(dx, dy)
      if (d < 1) continue
      // Set spring target — orb will be pulled here then spring back to home
      o.springTarget = { x, y }
      // Dramatic initial velocity lunge toward click point
      const speed = Math.min(d * 0.055, 16)
      Body.setVelocity(o.body, { x: dx / d * speed, y: dy / d * speed })
      // Reduce air friction so oscillation cycles are visible
      o.body.frictionAir = 0.004
      o.heat = Math.min(1, o.heat + 0.7)
    }
    adapt.mVel = Math.max(adapt.mVel, 4)
  }

  /** Set gravity direction from scene tilt — gx/gy in engine gravity units */
  function setTiltGravity(gx: number, gy: number) {
    if (engine) {
      engine.gravity.x = gx
      engine.gravity.y = gy
    }
  }

  /** Set card positions as gravity wells for particles and orbs */
  function setCardAttractors(pts: { x: number; y: number; mass: number }[]) {
    cardAttractors = pts
  }

  // ── Resize ──────────────────────────────────────────────────────
  function resize() {
    const c = canvasRef.value; if (!c) return
    dpr = Math.min(window.devicePixelRatio || 1, 2)
    W = c.clientWidth; H = c.clientHeight
    c.width = W * dpr; c.height = H * dpr
    ctx = c.getContext('2d')!
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  }

  // ── Frame loop ──────────────────────────────────────────────────
  function frame(ts: number) {
    if (!ctx) { raf = requestAnimationFrame(frame); return }
    if (!t0) { t0 = ts; tPrev = ts }
    const t = (ts - t0) / 1000
    const dt = Math.min((ts - tPrev) / 1000, 0.1)
    tPrev = ts

    pxSmooth.x += (pxTarget.x - pxSmooth.x) * 0.025
    pxSmooth.y += (pxTarget.y - pxSmooth.y) * 0.025

    stepAdapt(dt)
    if (engine) { M.Engine.update(engine, dt * 1000); stepForces(); if (cfg.enableKeyboard) stepKeyboard() }
    stepParticles(dt)

    drawClear()
    drawNebula(t)
    drawStarfield(t)
    drawParticles()
    drawConnections()
    drawOrbs()
    drawCursor()
    drawVignette()

    raf = requestAnimationFrame(frame)
  }

  // ── Lifecycle ───────────────────────────────────────────────────
  /** Call from onMounted. Sets up canvas, starts RAF loop. */
  async function init(): Promise<boolean> {
    resize()
    initStars()
    initParticles()
    initPhysics()

    window.addEventListener('resize', resize)
    window.addEventListener('mousemove', _onMouse)
    window.addEventListener('touchmove', _onTouch, { passive: true })
    window.addEventListener('deviceorientation', _onOrient)
    if (cfg.enableKeyboard) {
      window.addEventListener('keydown', _onKeyDown)
      window.addEventListener('keyup', _onKeyUp)
    }

    loaded.value = true
    raf = requestAnimationFrame(frame)
    return true
  }

  /** Call from onUnmounted. Stops loop, removes listeners, cleans up physics. */
  function destroy() {
    if (raf) cancelAnimationFrame(raf)
    try { if (engine) { M.Composite.clear(engine.world, false); M.Engine.clear(engine) } } catch { /* noop */ }
    window.removeEventListener('resize', resize)
    window.removeEventListener('mousemove', _onMouse)
    window.removeEventListener('touchmove', _onTouch)
    window.removeEventListener('deviceorientation', _onOrient)
    if (cfg.enableKeyboard) {
      window.removeEventListener('keydown', _onKeyDown)
      window.removeEventListener('keyup', _onKeyUp)
    }
  }

  /** Heat an orb by index (for external chime triggers etc.) */
  function heatOrb(idx: number, amount = 0.4) {
    if (orbs[idx]) orbs[idx].heat = Math.min(1, orbs[idx].heat + amount)
  }

  /** Get orb positions (for external audio proximity checks etc.) */
  function getOrbPositions(): { x: number; y: number; idx: number }[] {
    return orbs.map((o, i) => ({ x: o.body.position.x, y: o.body.position.y, idx: i }))
  }

  return {
    loaded,
    adapt,
    init,
    destroy,
    heatOrb,
    clickImpulse,
    setTiltGravity,
    setCardAttractors,
    getOrbPositions,
  }
}
