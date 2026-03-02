<template>
  <div class="trance-container" :style="{ '--blur': voiceActive ? '10px' : '0px' }">
    <canvas ref="canvasBus" class="spiral-canvas"></canvas>

    <div v-if="currentPhase === 'Coherence'" class="pacer-ring" :class="{ expanding: isExpanding }"></div>

    <div class="ui-layer">
      <nav v-if="currentPhase === 'Coherence'" class="hud-top">
        <div class="stat">
          <label>COHERENCE</label>
          <span :class="{ linked: coherenceScore > 70 }">{{ coherenceScore }}%</span>
        </div>
        <div class="stat">
          <label>PHASE</label>
          <span>{{ currentPhase.toUpperCase() }}</span>
        </div>
      </nav>

      <div v-if="currentPhase !== 'Coherence'" class="status-bar">
        <span class="phase-label">Phase: {{ currentPhase }}</span>
        <div class="progress-track"><div class="fill" :style="{ width: progress + '%' }"></div></div>
      </div>

      <div class="controls" v-if="!sessionActive">
        <h1>Binaural Induction Terminal</h1>
        <button @click="startSession" class="start-btn">BEGIN ENTRAINMENT</button>
      </div>

      <div class="interaction-zone" v-else>
        <transition name="fade" mode="out-in">
          <h2 v-if="currentPhase === 'Coherence'" :key="currentInstruction" class="instruction-text">
            {{ currentInstruction }}
          </h2>
          <p v-else class="instruction">{{ instructionText }}</p>
        </transition>

        <p v-if="currentPhase === 'Coherence'" class="sync-hint">Hold to match the pulse</p>

        <button
          @pointerdown="startSync"
          @pointerup="stopSync"
          class="sync-pad"
          :class="{ syncing: isSyncing }"
        >
          {{ currentPhase === 'Coherence' ? 'HOLD TO SYNC' : 'SYNC BREATH' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import * as Tone from 'tone';

// --- Star Field ---
const STAR_COUNT = 400;
const stars = [];

class Star {
  constructor(canvas) {
    this.reset(canvas);
  }
  reset(canvas) {
    this.x = (Math.random() - 0.5) * canvas.width * 2;
    this.y = (Math.random() - 0.5) * canvas.height * 2;
    this.z = canvas.width;
    this.px = 0;
    this.py = 0;
  }
  update(speed, canvas) {
    this.px = this.x / (this.z / canvas.width);
    this.py = this.y / (this.z / canvas.width);
    this.z -= speed;
    if (this.z < 1) this.reset(canvas);
  }
}

// --- State ---
const canvasBus = ref(null);
const sessionActive = ref(false);
const currentPhase = ref('Idle');
const progress = ref(0);
const voiceActive = ref(false);
const syncCount = ref(0);
const tunnelPulseStrength = ref(0);
const instructionText = ref('Follow the rhythm...');

// Coherence state
const coherenceScore = ref(0);
const isExpanding = ref(false);
const currentInstruction = ref('BREATHE IN');
const isSyncing = ref(false);

// --- Audio Engine ---
let osc, lfo, gainNode, meter, subBass, deepenLoop;
let swellOsc, swellGain, coherenceLoop;
let animFrameId;

const BREATH_CYCLE = 10;
const INHALE_TIME = 5;

const initAudio = () => {
  osc = new Tone.Oscillator(200, 'sine').start();
  gainNode = new Tone.Gain(0).toDestination();
  lfo = new Tone.LFO(12, 190, 210).connect(osc.frequency).start();
  osc.connect(gainNode);

  meter = new Tone.Meter();
  osc.connect(meter);

  subBass = new Tone.Synth({
    oscillator: { type: 'sine' },
    envelope: { attack: 0.01, decay: 0.3, sustain: 0, release: 0.5 },
  }).toDestination();
  subBass.volume.value = -6;
};

// --- Tunnel Rendering ---
const renderTunnel = () => {
  if (!canvasBus.value) return;
  const ctx = canvasBus.value.getContext('2d');
  const { width, height } = canvasBus.value;

  ctx.fillStyle = 'rgba(0, 0, 0, 0.15)';
  ctx.fillRect(0, 0, width, height);

  const currentSpeed = 5 + tunnelPulseStrength.value * 20;
  tunnelPulseStrength.value *= 0.9;

  ctx.strokeStyle = 'white';
  ctx.beginPath();
  stars.forEach(star => {
    star.update(currentSpeed, canvasBus.value);
    const x2d = star.x / (star.z / width) + width / 2;
    const y2d = star.y / (star.z / height) + height / 2;
    if (star.px !== 0) {
      ctx.moveTo(star.px + width / 2, star.py + height / 2);
      ctx.lineTo(x2d, y2d);
    }
  });
  ctx.stroke();

  animFrameId = requestAnimationFrame(renderTunnel);
};

// --- Deepen Beat Sync ---
const scheduleDeepenSequence = () => {
  Tone.getTransport().start();
  deepenLoop = new Tone.Loop((time) => {
    subBass.triggerAttackRelease('E1', '8n', time);
    Tone.getDraw().schedule(() => {
      tunnelPulseStrength.value = 1.0;
    }, time);
  }, '2n').start(0);
};

// --- Coherence Loop ---
const setupCoherenceLoop = () => {
  swellGain = new Tone.Gain(0).toDestination();
  swellOsc = new Tone.Oscillator(40, 'sine').connect(swellGain).start();

  coherenceLoop = Tone.getTransport().scheduleRepeat((time) => {
    swellGain.gain.rampTo(0.4, INHALE_TIME, time);

    Tone.getDraw().schedule(() => {
      currentInstruction.value = 'BREATHE IN';
      isExpanding.value = true;
    }, time);

    Tone.getDraw().schedule(() => {
      currentInstruction.value = 'BREATHE OUT';
      isExpanding.value = false;
    }, time + INHALE_TIME);

    swellGain.gain.rampTo(0, INHALE_TIME, time + INHALE_TIME);
  }, BREATH_CYCLE);

  Tone.getTransport().start();
};

// --- Phase Controller ---
const startSession = async () => {
  await Tone.start();
  initAudio();
  sessionActive.value = true;
  runInduction();
};

const runInduction = () => {
  currentPhase.value = 'Induction';
  instructionText.value = 'Breathe slowly. Let the rhythm guide you.';
  gainNode.gain.rampTo(0.5, 5);
  lfo.frequency.rampTo(6, 30);
  setTimeout(() => runCoherence(), 30000);
};

const runCoherence = () => {
  currentPhase.value = 'Coherence';
  setupCoherenceLoop();
};

const runDeepen = () => {
  if (currentPhase.value === 'Deepen') return;
  currentPhase.value = 'Deepen';
  lfo.frequency.rampTo(4.5, 60);
  if (swellOsc) swellOsc.stop();
  scheduleDeepenSequence();
};

// --- Sync Handlers ---
let syncStartTime = 0;

const startSync = () => {
  if (currentPhase.value === 'Coherence') {
    isSyncing.value = true;
    syncStartTime = Tone.getTransport().seconds;
    tunnelPulseStrength.value = 0.2;
  } else {
    // Pre-coherence: simple tap feedback
    syncCount.value++;
    progress.value = Math.min(progress.value + 5, 100);
    tunnelPulseStrength.value = 0.3;
    if (syncCount.value > 10) runDeepen();
  }
};

const stopSync = () => {
  if (currentPhase.value !== 'Coherence') return;

  const holdDuration = Tone.getTransport().seconds - syncStartTime;
  isSyncing.value = false;

  // Score accuracy: ideal hold is INHALE_TIME seconds
  const accuracy = 1 - Math.min(Math.abs(holdDuration - INHALE_TIME) / INHALE_TIME, 1);
  coherenceScore.value = Math.min(
    100,
    Math.round(coherenceScore.value * 0.7 + accuracy * 100 * 0.3)
  );

  tunnelPulseStrength.value = 0.3;
  syncCount.value++;
  progress.value = Math.min(progress.value + 5, 100);

  if (coherenceScore.value > 70 && syncCount.value > 5) {
    runDeepen();
  }
};

onMounted(() => {
  canvasBus.value.width = window.innerWidth;
  canvasBus.value.height = window.innerHeight;

  for (let i = 0; i < STAR_COUNT; i++) {
    stars.push(new Star(canvasBus.value));
  }

  renderTunnel();
});

onUnmounted(() => {
  if (animFrameId) cancelAnimationFrame(animFrameId);
  if (deepenLoop) deepenLoop.stop().dispose();
  if (coherenceLoop !== undefined) Tone.getTransport().clear(coherenceLoop);
  if (swellOsc) { swellOsc.stop(); swellOsc.dispose(); }
  if (swellGain) swellGain.dispose();
  Tone.getTransport().stop();
});
</script>

<style scoped>
.trance-container {
  background: #050505;
  height: 100vh;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  transition: filter 1s ease;
  filter: blur(var(--blur));
}

.spiral-canvas {
  position: absolute;
  z-index: 1;
}

/* Pacer ring */
.pacer-ring {
  position: absolute;
  width: 320px;
  height: 320px;
  border-radius: 50%;
  border: 2px solid rgba(74, 144, 226, 0.5);
  box-shadow: 0 0 20px rgba(74, 144, 226, 0.2);
  transform: scale(0.75);
  transition: transform 5s linear, box-shadow 5s linear;
  z-index: 2;
  pointer-events: none;
}

.pacer-ring.expanding {
  transform: scale(1.35);
  box-shadow: 0 0 40px rgba(74, 144, 226, 0.5);
}

.ui-layer {
  position: relative;
  z-index: 3;
  text-align: center;
  background: rgba(0, 0, 0, 0.4);
  padding: 2rem;
  border-radius: 20px;
  backdrop-filter: blur(5px);
  min-width: 280px;
}

/* HUD */
.hud-top {
  display: flex;
  justify-content: space-around;
  margin-bottom: 1.5rem;
  gap: 2rem;
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
}

.stat label {
  font-size: 0.65rem;
  letter-spacing: 0.15em;
  color: #666;
}

.stat span {
  font-size: 1.2rem;
  font-weight: 600;
  color: #4a90e2;
  transition: color 0.5s, text-shadow 0.5s;
}

.stat span.linked {
  color: #7fff7f;
  text-shadow: 0 0 12px rgba(127, 255, 127, 0.6);
}

/* Instruction text with crossfade */
.instruction-text {
  font-size: 1.6rem;
  letter-spacing: 0.2em;
  margin: 1rem 0;
  color: rgba(255, 255, 255, 0.9);
  text-shadow: 0 0 20px rgba(74, 144, 226, 0.5);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.8s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.sync-hint {
  font-size: 0.8rem;
  color: #555;
  margin-bottom: 0.5rem;
  letter-spacing: 0.1em;
}

/* Status bar (pre-coherence) */
.status-bar {
  margin-bottom: 1rem;
}

.phase-label {
  font-size: 0.85rem;
  color: #888;
}

.progress-track {
  width: 200px;
  height: 4px;
  background: #333;
  margin: 10px auto;
}

.fill {
  height: 100%;
  background: #4a90e2;
  transition: width 0.5s;
}

.sync-pad {
  margin-top: 20px;
  padding: 20px 40px;
  border-radius: 50px;
  border: 2px solid #4a90e2;
  background: transparent;
  color: white;
  cursor: pointer;
  letter-spacing: 0.1em;
  transition: all 0.3s;
}

.sync-pad:active,
.sync-pad.syncing {
  background: rgba(74, 144, 226, 0.25);
  border-color: #7fb8ff;
  box-shadow: 0 0 20px rgba(74, 144, 226, 0.4);
}

.instruction {
  color: #aaa;
  margin-bottom: 1rem;
}
</style>
