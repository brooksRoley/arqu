/**
 * Trance category definitions — data + canvas draw functions.
 *
 * Each category drives both audio (binaural beat params) and visuals
 * (canvas drawing routine). Draw functions are stateless: they receive
 * the canvas context, dimensions, time, mouse position, waveform data,
 * and the current view offset from drag interaction.
 */

export interface ViewOffset {
  x: number
  y: number
}

export interface TranceCategory {
  label: string
  formula: string
  words: string[]
  color: string
  colorBright: string
  beatHz: number
  carrier: number
  draw: (
    ctx: CanvasRenderingContext2D,
    w: number,
    h: number,
    t: number,
    mx: number,
    my: number,
    wf: Uint8Array | null,
    vo: ViewOffset,
  ) => void
}

function audioEnergy(wf: Uint8Array | null): number {
  if (!wf) return 0
  let sum = 0
  for (let i = 0; i < wf.length; i++) sum += Math.abs(wf[i] - 128)
  return sum / wf.length / 128
}

/*
 * GAMMA BINAURAL BEAT MAPPING PER CATEGORY
 * ─────────────────────────────────────────
 * Focus:      40 Hz beat @ 220 Hz carrier — classic gamma, peak concentration
 * Relaxation: 32 Hz beat @ 180 Hz carrier — low gamma boundary, calm alertness
 * Deepening:  36 Hz beat @ 160 Hz carrier — mid gamma, trance induction
 * Sensory:    44 Hz beat @ 250 Hz carrier — high gamma, vivid imagery / creativity
 * Suggestion: 38 Hz beat @ 200 Hz carrier — steady gamma, suggestibility / receptivity
 */

export const categories: Record<string, TranceCategory> = {

  // ── Focus: exponential spiral with center glow + concentric rings ──
  focus: {
    label: 'Focus & Visual Engagement',
    formula: 'r(\u03B8) = a\u00B7e^(b\u03B8) \u00B7 cos(\u03C9t)',
    words: ['spiral', 'spinning', 'focus', 'stare deeper', 'center', 'fixate', 'gaze', 'swirling'],
    color: 'rgba(123, 94, 167, 0.5)',
    colorBright: '#7b5ea7',
    beatHz: 40,
    carrier: 220,
    draw(ctx, w, h, t, mx, my, wf, vo) {
      const cx = w / 2 + vo.x, cy = h / 2 + vo.y, ae = audioEnergy(wf)
      for (let layer = 0; layer < 3; layer++) {
        ctx.beginPath()
        const off = layer * 0.7 + t * 0.3
        for (let i = 0; i <= 800; i++) {
          const theta = (i / 800) * 12 * Math.PI + off
          const r = 2 * Math.exp(0.12 * theta) * (1 + (0.15 + ae * 0.2) * Math.sin(t * 2 + theta * 0.5))
          const x = cx + r * Math.cos(theta), y = cy + r * Math.sin(theta)
          i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)
        }
        ctx.strokeStyle = `rgba(123,94,167,${0.15 - layer * 0.04 + ae * 0.08})`
        ctx.lineWidth = 1.5 - layer * 0.3
        ctx.stroke()
      }
      // Center glow
      ctx.beginPath()
      ctx.arc(cx, cy, 4 + 2 * Math.sin(t * 3) + ae * 8, 0, Math.PI * 2)
      ctx.fillStyle = `rgba(200,180,240,${0.6 + 0.3 * Math.sin(t * 3)})`
      ctx.fill()
      // Mouse-proximity rings
      const inf = Math.max(0, 1 - Math.hypot(mx - cx, my - cy) / (w * 0.4))
      for (let r = 0; r < 5; r++) {
        ctx.beginPath()
        ctx.arc(cx, cy, 30 + r * 40 - inf * 15 + 5 * Math.sin(t * 2 + r) + ae * 10, 0, Math.PI * 2)
        ctx.strokeStyle = `rgba(123,94,167,${0.08 + inf * 0.1})`
        ctx.lineWidth = 0.8
        ctx.stroke()
      }
    },
  },

  // ── Relaxation: layered sine waves + orbiting particles ──
  relaxation: {
    label: 'Relaxation & Physical Surrender',
    formula: 'y(t) = A\u00B7e^(-\u03BBt) \u00B7 sin(\u03C9t + \u03C6)',
    words: ['relax', 'soothe', 'heavy', 'close', 'drift', 'float', 'let go', 'release'],
    color: 'rgba(58, 107, 138, 0.5)',
    colorBright: '#3a6b8a',
    beatHz: 32,
    carrier: 180,
    draw(ctx, w, h, t, _mx, _my, wf, vo) {
      const cy = h / 2 + vo.y * 0.4, ae = audioEnergy(wf)
      for (let wave = 0; wave < 6; wave++) {
        ctx.beginPath()
        const phi = wave * 0.8 + t * 0.2
        for (let x = 0; x <= w; x += 2) {
          const nX = (x / w) * 8
          const env = h * 0.3 * Math.exp(-0.4 * Math.abs(nX - 4))
          const y = cy + env * Math.sin(2.5 * nX + phi + t * 0.5) * (1 + ae * 0.3) + wave * 8
          x === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)
        }
        ctx.strokeStyle = `rgba(58,107,138,${0.12 - wave * 0.015 + ae * 0.05})`
        ctx.lineWidth = 2 - wave * 0.2
        ctx.stroke()
      }
      for (let p = 0; p < 20; p++) {
        const s = p * 137.508
        const px = w * 0.2 + w * 0.6 * ((Math.sin(s) + 1) / 2)
        const py = cy + h * 0.3 * Math.sin(s * 0.7 + t * 0.3) * Math.exp(-0.1 * (t % 10))
        ctx.beginPath()
        ctx.arc(px, py, 1.5 + Math.sin(t + s) * 0.8 + ae * 3, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(100,170,210,${0.15 + 0.1 * Math.sin(t + s)})`
        ctx.fill()
      }
    },
  },

  // ── Deepening: sigmoid circles + radiating lines ──
  deepening: {
    label: 'Deepening Trance',
    formula: 'd(t) = D / (1 + e^(k\u00B7(t - t\u2080)))',
    words: ['deeper', 'deeper and deeper', 'descend', 'sink', 'trance', 'hypnotic trance', 'deep trance', 'unconscious'],
    color: 'rgba(26, 26, 62, 0.8)',
    colorBright: '#2a2a5e',
    beatHz: 36,
    carrier: 160,
    draw(ctx, w, h, t, _mx, _my, wf, vo) {
      const cx = w / 2 + vo.x, cy = h / 2 + vo.y, ae = audioEnergy(wf)
      for (let i = 12; i >= 0; i--) {
        const sig = 1 / (1 + Math.exp(5 * ((t * 0.4) % (12 * 0.8 + 4) - i * 0.8)))
        const r = sig * Math.min(w, h) * 0.45 + 5 + ae * 20
        ctx.beginPath()
        ctx.arc(cx, cy, Math.max(r, 2), 0, Math.PI * 2)
        const d = 1 - i / 12
        ctx.fillStyle = `rgba(${20 + d * 20},${15 + d * 15},${50 + d * 40},${0.08 + d * 0.04})`
        ctx.fill()
        ctx.strokeStyle = `rgba(80,70,130,${0.06 + sig * 0.08 + ae * 0.06})`
        ctx.lineWidth = 0.6
        ctx.stroke()
      }
      for (let l = 0; l < 8; l++) {
        const a = (l / 8) * Math.PI * 2 + t * 0.1
        const len = 50 + 150 * ((Math.sin(t * 0.5 + l) + 1) / 2) + ae * 60
        ctx.beginPath()
        ctx.moveTo(cx + 20 * Math.cos(a), cy + 20 * Math.sin(a))
        ctx.lineTo(cx + len * Math.cos(a), cy + len * Math.sin(a))
        ctx.strokeStyle = `rgba(60,50,120,${0.12 + ae * 0.1})`
        ctx.lineWidth = 0.5
        ctx.stroke()
      }
    },
  },

  // ── Sensory: grid-based vector field (4-harmonic sum) ──
  sensory: {
    label: 'Sensory & Imaginative Guidance',
    formula: 'f(x,t) = \u03A3 sin(n\u00B7x + t) / n',
    words: ['imagine', 'pretend', 'visualize', 'breathe deeply', 'gentle breeze', 'flowing', 'washes away', 'refreshing'],
    color: 'rgba(90, 138, 107, 0.5)',
    colorBright: '#5a8a6b',
    beatHz: 44,
    carrier: 250,
    draw(ctx, w, h, t, _mx, _my, wf, vo) {
      const gs = 28, ae = audioEnergy(wf)
      for (let gy = 0; gy < Math.ceil(h / gs) + 1; gy++) {
        for (let gx = 0; gx < Math.ceil(w / gs) + 1; gx++) {
          let val = 0
          for (let n = 1; n <= 4; n++) {
            val += Math.sin(n * gx * 0.3 + t * 0.5 + n) / n + Math.cos(n * gy * 0.25 + t * 0.4 + n * 2) / n
          }
          const norm = (val + 3) / 6
          const len = norm * gs * (0.8 + ae * 0.5)
          const angle = val * Math.PI + t * 0.2
          const x = gx * gs, y = gy * gs
          ctx.beginPath()
          ctx.moveTo(x, y)
          ctx.lineTo(x + len * Math.cos(angle), y + len * Math.sin(angle))
          ctx.strokeStyle = `rgba(90,${100 + norm * 80},107,${0.06 + norm * 0.08})`
          ctx.lineWidth = 0.6 + norm * 0.8
          ctx.stroke()
        }
      }
      const bc = Math.sin(t * 0.8) * 0.5 + 0.5
      ctx.beginPath()
      ctx.arc(w / 2 + vo.x, h / 2 + vo.y, 40 + bc * 80 + ae * 30, 0, Math.PI * 2)
      ctx.strokeStyle = `rgba(120,200,150,${0.08 + bc * 0.1 + ae * 0.08})`
      ctx.lineWidth = 1.5
      ctx.stroke()
    },
  },

  // ── Suggestion: harmonic cosines + nodal points + radial vignette ──
  suggestion: {
    label: 'Suggestion & Reinforcement',
    formula: 's(t) = \u03A3 A\u2099 \u00B7 cos(n\u00B7\u03C9\u00B7t)',
    words: ['allow', 'effortless', 'calm', 'tranquil', 'peaceful', 'serene', 'because'],
    color: 'rgba(138, 122, 90, 0.5)',
    colorBright: '#8a7a5a',
    beatHz: 38,
    carrier: 200,
    draw(ctx, w, h, t, _mx, _my, wf, vo) {
      const cx = w / 2 + vo.x, cy = h / 2 + vo.y, ae = audioEnergy(wf)
      for (let n = 1; n <= 5; n++) {
        const An = 1 / n
        ctx.beginPath()
        for (let x = 0; x <= w; x += 2) {
          const nX = (x / w) * Math.PI * 4
          const y = cy + h * (0.15 + ae * 0.05) * An * Math.cos(n * 1.2 * t) * Math.sin(n * nX)
          x === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)
        }
        ctx.strokeStyle = `rgba(180,160,110,${0.08 + An * 0.06 + ae * 0.04})`
        ctx.lineWidth = 1.2
        ctx.stroke()
      }
      // Nodal points
      for (let nd = 0; nd < 8; nd++) {
        const nx = ((nd + 1) / 9) * w
        let itf = 0
        for (let n = 1; n <= 5; n++) itf += (1 / n) * Math.cos(n * 1.2 * t) * Math.sin(n * (nx / w) * Math.PI * 4)
        ctx.beginPath()
        ctx.arc(nx, cy + itf * h * 0.15, 2 + Math.abs(itf) * 4 + ae * 5, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(220,200,140,${0.1 + Math.abs(itf) * 0.25})`
        ctx.fill()
      }
      // Radial vignette
      const grad = ctx.createRadialGradient(cx, cy, 10, cx, cy, Math.min(w, h) * 0.4)
      grad.addColorStop(0, `rgba(138,122,90,${0.04 + 0.02 * Math.sin(t)})`)
      grad.addColorStop(1, 'rgba(138,122,90,0)')
      ctx.fillStyle = grad
      ctx.fillRect(0, 0, w, h)
    },
  },
}

const categoryKeys = Object.keys(categories)

/** Pick a random category + word pair */
export function pickRandom(): { catKey: string; word: string } {
  const k = categoryKeys[Math.floor(Math.random() * categoryKeys.length)]
  const cat = categories[k]
  return { catKey: k, word: cat.words[Math.floor(Math.random() * cat.words.length)] }
}
