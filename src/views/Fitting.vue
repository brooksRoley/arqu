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
        </defs>

        <!-- HEAD -->
        <ellipse
          :cx="cx"
          :cy="headY"
          :rx="headW"
          :ry="headH"
          fill="url(#skinGrad)"
        />
        <!-- Hair suggestion -->
        <ellipse
          :cx="cx"
          :cy="headY - headH * 0.6"
          :rx="headW * 0.95"
          :ry="headH * 0.55"
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

        <!-- SHOULDERS -->
        <path
          :d="shoulderPath"
          fill="url(#skinGrad)"
        />

        <!-- ARMS left -->
        <path :d="leftArmPath" fill="url(#skinGrad)" />
        <!-- ARMS right -->
        <path :d="rightArmPath" fill="url(#skinGrad)" />

        <!-- TORSO skin base (visible above/below suit) -->
        <path :d="torsoSkinPath" fill="url(#skinGrad)" />

        <!-- LEGS -->
        <path :d="leftLegPath" fill="url(#skinGrad)" />
        <path :d="rightLegPath" fill="url(#skinGrad)" />

        <!-- FEET -->
        <ellipse
          :cx="cx - hipW * 0.28"
          :cy="legBottom + 14"
          rx="14"
          ry="8"
          fill="url(#skinGrad)"
        />
        <ellipse
          :cx="cx + hipW * 0.28"
          :cy="legBottom + 14"
          rx="14"
          ry="8"
          fill="url(#skinGrad)"
        />

        <!-- SWIMSUIT TOP -->
        <path
          :d="suitTopPath"
          fill="url(#suitTopGrad)"
          class="suit-zone"
          :class="{ active: activeZone === 'bust' }"
          @click.stop="selectZone('bust')"
        />

        <!-- SWIMSUIT BOTTOM -->
        <path
          :d="suitBottomPath"
          fill="url(#suitBotGrad)"
          class="suit-zone"
          :class="{ active: activeZone === 'hips' || activeZone === 'bottomCoverage' }"
          @click.stop="selectZone('hips')"
        />

        <!-- ZONE HIGHLIGHT RINGS -->
        <path
          v-if="activeZone === 'bust'"
          :d="suitTopPath"
          fill="none"
          stroke="white"
          stroke-width="2"
          opacity="0.8"
        />
        <path
          v-if="activeZone === 'hips' || activeZone === 'bottomCoverage'"
          :d="suitBottomPath"
          fill="none"
          stroke="white"
          stroke-width="2"
          opacity="0.8"
        />

        <!-- ZONE LABELS -->
        <text :x="cx" :y="shoulderY - 6" text-anchor="middle" class="zone-label" @click.stop="selectZone('bust')">tap suit to adjust</text>
      </svg>
    </div>

    <!-- CONTROLS PANEL -->
    <div class="controls-panel">
      <section class="control-section">
        <h3>Body</h3>

        <label>Height <span>{{ heightLabel }}</span></label>
        <input type="range" v-model.number="body.height" min="58" max="78" />

        <label>Build <span>{{ buildLabel }}</span></label>
        <input type="range" v-model.number="body.build" min="1" max="10" />

        <label>Bust <span>{{ body.bust }}</span></label>
        <input type="range" v-model.number="body.bust" min="28" max="54" />

        <label>Waist <span>{{ body.waist }}"</span></label>
        <input type="range" v-model.number="body.waist" min="22" max="54" />

        <label>Hips <span>{{ body.hips }}"</span></label>
        <input type="range" v-model.number="body.hips" min="30" max="62" />
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

        <label>Hair</label>
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
      </section>

      <section class="control-section">
        <h3>Suit</h3>

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
            :class="{ selected: suit.topStyle === style }"
            @click="suit.topStyle = style"
          >{{ style }}</button>
        </div>

        <label>Bottom Rise</label>
        <div class="option-row">
          <button
            v-for="rise in riseOptions"
            :key="rise"
            :class="{ selected: suit.rise === rise }"
            @click="suit.rise = rise"
          >{{ rise }}</button>
        </div>

        <label>Bottom Coverage</label>
        <div class="option-row">
          <button
            v-for="cov in coverageOptions"
            :key="cov"
            :class="{ selected: suit.coverage === cov }"
            @click="suit.coverage = cov"
          >{{ cov }}</button>
        </div>
      </section>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      activeZone: null,

      body: {
        height: 65,   // inches
        build: 5,     // 1-10 lean to curvy
        bust: 38,
        waist: 32,
        hips: 42
      },

      skinColor: '#C68642',
      skinShadow: '#A0522D',
      hairColor: '#3B1F0A',

      suitColor: '#C0458A',
      suitColorDark: '#8B1A5E',

      suit: {
        topStyle: 'underwire',
        rise: 'mid',
        coverage: 'full'
      },

      skinTones: [
        { color: '#FDDBB4', shadow: '#E8B88A' },
        { color: '#EDB98A', shadow: '#C88B5A' },
        { color: '#C68642', shadow: '#A0522D' },
        { color: '#8D5524', shadow: '#6B3A0F' },
        { color: '#4A2912', shadow: '#2E1508' },
        { color: '#FEE0C0', shadow: '#ECBF98' }
      ],

      hairColors: ['#3B1F0A', '#6B3A0F', '#C49A3C', '#E8D5A3', '#1A1A1A', '#8B0000', '#6B478B', '#4A90D9'],

      suitOptions: [
        { color: '#C0458A', dark: '#8B1A5E' },
        { color: '#2E86AB', dark: '#1A5276' },
        { color: '#E8453C', dark: '#B03030' },
        { color: '#27AE60', dark: '#1A7A42' },
        { color: '#F39C12', dark: '#B07A0A' },
        { color: '#1A1A2E', dark: '#0D0D1A' },
        { color: '#FFFFFF', dark: '#C8C8C8' },
        { color: '#E8C3E8', dark: '#C090C0' }
      ],

      topStyles: ['underwire', 'bralette', 'bandeau', 'halter'],
      riseOptions: ['low', 'mid', 'high', 'ultra'],
      coverageOptions: ['cheeky', 'moderate', 'full', 'boy-short']
    }
  },

  computed: {
    // Layout constants derived from body sliders
    cx() { return 150 },

    // Scale height: 58" -> 0.85, 78" -> 1.15
    heightScale() { return 0.85 + (this.body.height - 58) / 20 * 0.30 },

    // Build affects width multipliers
    buildScale() { return 0.80 + (this.body.build - 1) / 9 * 0.55 },

    svgHeight() { return Math.round(700 * this.heightScale) },

    // Derived measurements normalized to SVG space
    bustW()  { return (this.body.bust  / 38) * 74 * this.buildScale },
    waistW() { return (this.body.waist / 32) * 52 * this.buildScale },
    hipW()   { return (this.body.hips  / 42) * 80 * this.buildScale },

    // Key Y positions (all scale with height)
    headH() { return 36 * this.heightScale },
    headW() { return 26 },
    headY() { return 46 * this.heightScale },
    neckW() { return 22 },
    neckH() { return 18 * this.heightScale },

    shoulderY() { return this.headY + this.headH + this.neckH },
    bustY()     { return this.shoulderY + 18 * this.heightScale },
    underbustY(){ return this.bustY + 54 * this.heightScale * (this.body.bust / 38) * 0.5 + 20 },
    waistY()    { return this.underbustY + 40 * this.heightScale },
    hipTopY()   { return this.waistY + 20 * this.heightScale },
    hipBottomY(){ return this.hipTopY + 70 * this.heightScale },
    crotchY()   { return this.hipBottomY },
    legBottom() { return this.crotchY + 200 * this.heightScale },

    shoulderPath() {
      const sy = this.shoulderY
      const sw = this.bustW * 0.95
      const cx = this.cx
      return `
        M ${cx - sw} ${sy + 24}
        Q ${cx - sw * 1.05} ${sy} ${cx - sw * 0.55} ${sy - 6}
        L ${cx + sw * 0.55} ${sy - 6}
        Q ${cx + sw * 1.05} ${sy} ${cx + sw} ${sy + 24}
        Q ${cx + this.waistW * 0.6} ${this.waistY} ${cx + this.waistW / 2} ${this.waistY}
        L ${cx - this.waistW / 2} ${this.waistY}
        Q ${cx - this.waistW * 0.6} ${this.waistY} ${cx - sw} ${sy + 24}
        Z
      `
    },

    torsoSkinPath() {
      const cx = this.cx
      const bw = this.bustW / 2
      const ww = this.waistW / 2
      const hw = this.hipW / 2
      return `
        M ${cx - bw} ${this.bustY}
        Q ${cx - ww * 1.1} ${this.waistY} ${cx - ww} ${this.waistY}
        Q ${cx - hw * 1.05} ${this.hipTopY} ${cx - hw} ${this.hipBottomY}
        L ${cx + hw} ${this.hipBottomY}
        Q ${cx + hw * 1.05} ${this.hipTopY} ${cx + ww} ${this.waistY}
        Q ${cx + ww * 1.1} ${this.waistY} ${cx + bw} ${this.bustY}
        Z
      `
    },

    leftArmPath() {
      const cx = this.cx
      const sw = this.bustW * 0.95
      const armW = 16 * this.buildScale * 0.85
      const ax = cx - sw
      return `
        M ${ax - armW * 0.6} ${this.shoulderY + 12}
        Q ${ax - armW} ${this.shoulderY + 60 * this.heightScale} ${ax - armW * 0.5} ${this.waistY + 10}
        L ${ax + armW * 0.4} ${this.waistY + 10}
        Q ${ax + armW * 0.2} ${this.shoulderY + 60 * this.heightScale} ${ax + armW * 0.6} ${this.shoulderY + 12}
        Z
      `
    },

    rightArmPath() {
      const cx = this.cx
      const sw = this.bustW * 0.95
      const armW = 16 * this.buildScale * 0.85
      const ax = cx + sw
      return `
        M ${ax + armW * 0.6} ${this.shoulderY + 12}
        Q ${ax + armW} ${this.shoulderY + 60 * this.heightScale} ${ax + armW * 0.5} ${this.waistY + 10}
        L ${ax - armW * 0.4} ${this.waistY + 10}
        Q ${ax - armW * 0.2} ${this.shoulderY + 60 * this.heightScale} ${ax - armW * 0.6} ${this.shoulderY + 12}
        Z
      `
    },

    leftLegPath() {
      const cx = this.cx
      const hw = this.hipW / 2
      const lw = hw * 0.52
      const lx = cx - hw * 0.28
      return `
        M ${cx - hw * 0.05} ${this.crotchY}
        L ${cx - hw * 0.6} ${this.crotchY}
        Q ${lx - lw * 0.55} ${this.crotchY + 80 * this.heightScale} ${lx - lw * 0.45} ${this.legBottom}
        L ${lx + lw * 0.35} ${this.legBottom}
        Q ${lx + lw * 0.55} ${this.crotchY + 80 * this.heightScale} ${cx + hw * 0.05} ${this.crotchY}
        Z
      `
    },

    rightLegPath() {
      const cx = this.cx
      const hw = this.hipW / 2
      const lw = hw * 0.52
      const lx = cx + hw * 0.28
      return `
        M ${cx + hw * 0.05} ${this.crotchY}
        L ${cx + hw * 0.6} ${this.crotchY}
        Q ${lx + lw * 0.55} ${this.crotchY + 80 * this.heightScale} ${lx + lw * 0.45} ${this.legBottom}
        L ${lx - lw * 0.35} ${this.legBottom}
        Q ${lx - lw * 0.55} ${this.crotchY + 80 * this.heightScale} ${cx - hw * 0.05} ${this.crotchY}
        Z
      `
    },

    // Swimsuit top path — changes with topStyle
    suitTopPath() {
      const cx = this.cx
      const bw = this.bustW / 2
      const ww = this.waistW / 2
      const by = this.bustY
      const uby = this.underbustY
      const style = this.suit.topStyle

      if (style === 'bandeau') {
        // Straight band across
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
        // Triangles up to center neck point
        const neckPt = this.shoulderY - 16
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
        // Softer, less structured
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

      // underwire (default) — structured curved cups
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
    },

    // Swimsuit bottom path — changes with rise + coverage
    suitBottomPath() {
      const cx = this.cx
      const hw = this.hipW / 2
      const ww = this.waistW / 2
      const cov = this.suit.coverage
      const rise = this.suit.rise

      const riseOffset = { low: 30, mid: 14, high: 2, ultra: -8 }[rise] ?? 14
      const topY = this.hipTopY + riseOffset
      const botY = this.hipBottomY

      // Side coverage multiplier
      const sideIn = { cheeky: 0.55, moderate: 0.72, full: 0.88, 'boy-short': 0.95 }[cov] ?? 0.88

      return `
        M ${cx - ww * 0.85} ${topY}
        Q ${cx - hw * 1.02} ${topY + (botY - topY) * 0.3} ${cx - hw * sideIn} ${botY - 4}
        Q ${cx - hw * 0.3} ${botY + 10} ${cx} ${botY + 8}
        Q ${cx + hw * 0.3} ${botY + 10} ${cx + hw * sideIn} ${botY - 4}
        Q ${cx + hw * 1.02} ${topY + (botY - topY) * 0.3} ${cx + ww * 0.85} ${topY}
        Q ${cx} ${topY - 8} ${cx - ww * 0.85} ${topY}
        Z
      `
    },

    heightLabel() {
      const ft = Math.floor(this.body.height / 12)
      const inch = this.body.height % 12
      return `${ft}'${inch}"`
    },

    buildLabel() {
      const labels = ['', 'very lean', 'lean', 'slim', 'athletic', 'average', 'soft', 'curvy', 'full', 'plus', 'extra plus']
      return labels[this.body.build] || ''
    }
  },

  methods: {
    selectZone(zone) {
      this.activeZone = zone
    },
    clearZone() {
      this.activeZone = null
    }
  }
}
</script>

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
  accent-color: #C0458A;
  cursor: pointer;
  margin-bottom: 4px;
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

.option-row button:hover {
  background: #3a3a4e;
  color: #eee;
}

.option-row button.selected {
  background: #C0458A;
  color: white;
  border-color: #C0458A;
}
</style>
