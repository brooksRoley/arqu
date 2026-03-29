<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { usePollStore } from '@/composables/usePollStore'
import { useMeditation } from '@/composables/useMeditation'
import { useCosmicPhysics } from '@/composables/useCosmicPhysics'
import type { PollAnswers } from '@/composables/usePollStore'

const router = useRouter()
const { answers, token, setAnswer, submitPoll, resetPoll } = usePollStore()
const med = useMeditation()

// ── Cosmic physics background ────────────────────────────────────
const bgCanvas = ref<HTMLCanvasElement>()
const { init: initCosmic, destroy: destroyCosmic } = useCosmicPhysics(bgCanvas, {
  particleCount: 120,
  starCount: 100,
  enableKeyboard: false,
  enableMouseInteract: true,
  clearAlpha: 0.08,
  mouseAttractForce: 0.5,
})

// ── Stage management ─────────────────────────────────────────────
type Stage = 'home' | 'poll'
const stage = ref<Stage>('home')
const showMeditation = ref(false)

function openMeditation() {
  showMeditation.value = true
}

function closeMeditation() {
  med.stop()
  showMeditation.value = false
}

// ── Poll logic (inlined from PollView) ───────────────────────────
const pollStep = ref(1)
const pollDirection = ref<'forward' | 'back'>('forward')

type QuestionOption = { value: string; label: string; sublabel: string }

const questions: Array<{
  key: keyof PollAnswers
  text: string
  options: QuestionOption[]
}> = [
  {
    key: 'q1',
    text: 'Did you often create detailed imaginary worlds or friends, and do you find it easy now to get so lost in a book, movie, or daydream that the real world fades away?',
    options: [
      { value: 'vivid-dreamer', label: 'Absolutely', sublabel: "I've always had a rich inner world" },
      { value: 'balanced-escapist', label: 'Somewhat', sublabel: 'I can get lost but stay anchored' },
      { value: 'grounded-realist', label: 'Not really', sublabel: 'I stay grounded in the present' },
    ],
  },
  {
    key: 'q2',
    text: "Have you ever experienced moments where stressful or unpleasant events caused you to mentally 'check out' or go numb, almost like forgetting they happened in the moment?",
    options: [
      { value: 'frequent-dissociation', label: 'Yes, fairly often', sublabel: "It's how I cope" },
      { value: 'occasional-detachment', label: 'Sometimes', sublabel: 'In particularly intense moments' },
      { value: 'fully-present', label: 'Rarely', sublabel: "I tend to stay present even when it's hard" },
    ],
  },
  {
    key: 'q3',
    text: 'Growing up, were you encouraged to do a lot of pretend play or storytelling, and how does that influence how you handle creative or relaxing activities?',
    options: [
      { value: 'creative-storyteller', label: 'Very much so', sublabel: 'Creativity is central to how I relax' },
      { value: 'structured-play', label: 'Some', sublabel: 'I blend structured and imaginative approaches' },
      { value: 'independent-explorer', label: 'Not much', sublabel: 'I tend toward more pragmatic approaches' },
    ],
  },
  {
    key: 'q4',
    text: 'Do you sometimes find your mind going completely blank during routine tasks or conversations, rather than filling with vivid thoughts or stories?',
    options: [
      { value: 'blank-slate', label: 'Yes, often', sublabel: 'I zone out into a kind of mental static' },
      { value: 'thought-rich', label: "No — my mind's usually active", sublabel: 'Filled with thoughts or imagery' },
      { value: 'context-dependent', label: 'It depends', sublabel: 'Varies a lot by context' },
    ],
  },
]

const currentQuestion = computed(() => questions[pollStep.value - 1])
const pollProgress = computed(() => Math.min((pollStep.value - 1) / questions.length, 1))

function selectAnswer(value: string) {
  const q = currentQuestion.value
  setAnswer(q.key, value as PollAnswers[typeof q.key])
  if (pollStep.value < questions.length) {
    pollDirection.value = 'forward'
    pollStep.value++
  } else {
    submitPoll()
    pollStep.value = 1
    stage.value = 'home'
  }
}

function pollBack() {
  if (pollStep.value <= 1) {
    stage.value = 'home'
    return
  }
  pollDirection.value = 'back'
  pollStep.value--
}

function retakePoll() {
  resetPoll()
  pollStep.value = 1
  pollDirection.value = 'forward'
  stage.value = 'poll'
}

// ── Session data ─────────────────────────────────────────────────
interface SessionOption {
  route: string
  label: string
  description: string
  icon: string
  recommended?: boolean
}

const themeSessions: Record<string, SessionOption[]> = {
  dreamlike: [
    { route: '/webaudio', label: 'Star Tunnel', description: 'Immersive star field with binaural entrainment', icon: '✦', recommended: true },
    { route: '/zeromind', label: 'Zeromind', description: 'Generative visuals with streaming text', icon: '🔮' },
    { route: '/spiral', label: 'Spiral', description: 'Hypnotic spiral with trance words', icon: '🌀' },
    { route: '/trance', label: 'Tone Engine', description: 'Raw binaural tone laboratory', icon: '🎧' },
  ],
  electric: [
    { route: '/zeromind', label: 'Zeromind', description: 'Generative visuals with streaming text', icon: '🔮', recommended: true },
    { route: '/webaudio', label: 'Star Tunnel', description: 'Immersive star field with binaural entrainment', icon: '✦' },
    { route: '/spiral', label: 'Spiral', description: 'Hypnotic spiral with trance words', icon: '🌀' },
    { route: '/trance', label: 'Tone Engine', description: 'Raw binaural tone laboratory', icon: '🎧' },
  ],
  void: [
    { route: '/spiral', label: 'Spiral', description: 'Hypnotic spiral — minimalist and absorbing', icon: '🌀', recommended: true },
    { route: '/trance', label: 'Tone Engine', description: 'Raw binaural tone laboratory', icon: '🎧' },
    { route: '/webaudio', label: 'Star Tunnel', description: 'Immersive star field with binaural entrainment', icon: '✦' },
    { route: '/zeromind', label: 'Zeromind', description: 'Generative visuals with streaming text', icon: '🔮' },
  ],
  organic: [
    { route: '/trance', label: 'Tone Engine', description: 'Binaural tone engine — grounded and tactile', icon: '🎧', recommended: true },
    { route: '/webaudio', label: 'Star Tunnel', description: 'Immersive star field with binaural entrainment', icon: '✦' },
    { route: '/spiral', label: 'Spiral', description: 'Hypnotic spiral with trance words', icon: '🌀' },
    { route: '/zeromind', label: 'Zeromind', description: 'Generative visuals with streaming text', icon: '🔮' },
  ],
  liminal: [
    { route: '/webaudio', label: 'Star Tunnel', description: 'Ambient star drift with entrainment layers', icon: '✦', recommended: true },
    { route: '/zeromind', label: 'Zeromind', description: 'Generative visuals with streaming text', icon: '🔮' },
    { route: '/spiral', label: 'Spiral', description: 'Hypnotic spiral with trance words', icon: '🌀' },
    { route: '/trance', label: 'Tone Engine', description: 'Raw binaural tone laboratory', icon: '🎧' },
  ],
}

const themeLabels: Record<string, string> = {
  dreamlike: 'Dreamlike',
  electric: 'Electric',
  void: 'The Void',
  organic: 'Organic',
  liminal: 'Liminal',
}

const sessions = computed(() => {
  if (!token.value) return []
  return themeSessions[token.value.theme] || themeSessions.liminal
})

const recommendedSession = computed(() => sessions.value.find((s) => s.recommended) || sessions.value[0])
const otherSessions = computed(() => sessions.value.filter((s) => !s.recommended))

// Featured card adapts based on state
const featuredTitle = computed(() =>
  token.value && recommendedSession.value ? recommendedSession.value.label : 'Discover Your Experience'
)
const featuredDesc = computed(() =>
  token.value && recommendedSession.value
    ? recommendedSession.value.description
    : 'A quick introduction to find the right session for your mind'
)

function handleFeaturedClick() {
  if (token.value && recommendedSession.value) {
    router.push(recommendedSession.value.route)
  } else {
    stage.value = 'poll'
  }
}

// (Cosmic physics background replaces old ambient particle drift)

// ── Scene drag tilt ──────────────────────────────────────────────
const sceneTilt = reactive({ x: 0, y: 0 })
let tiltTarget = { x: 0, y: 0 }
let isDragging = false
let lastDragX = 0
let lastDragY = 0
let springId: number | null = null

function runSpring() {
  tiltTarget.x *= 0.87
  tiltTarget.y *= 0.87
  sceneTilt.x += (tiltTarget.x - sceneTilt.x) * 0.11
  sceneTilt.y += (tiltTarget.y - sceneTilt.y) * 0.11
  if (Math.abs(sceneTilt.x) > 0.02 || Math.abs(sceneTilt.y) > 0.02) {
    springId = requestAnimationFrame(runSpring)
  } else {
    sceneTilt.x = 0
    sceneTilt.y = 0
    springId = null
  }
}

function startSpring() {
  if (springId) cancelAnimationFrame(springId)
  springId = requestAnimationFrame(runSpring)
}

function onMouseDown(e: MouseEvent) {
  isDragging = true
  lastDragX = e.clientX
  lastDragY = e.clientY
  if (springId) { cancelAnimationFrame(springId); springId = null }
}

function onMouseMove(e: MouseEvent) {
  if (!isDragging) return
  const dx = e.clientX - lastDragX
  const dy = e.clientY - lastDragY
  lastDragX = e.clientX
  lastDragY = e.clientY
  tiltTarget.y = Math.max(-9, Math.min(9, tiltTarget.y + dx * 0.06))
  tiltTarget.x = Math.max(-6, Math.min(6, tiltTarget.x - dy * 0.06))
  sceneTilt.x = tiltTarget.x
  sceneTilt.y = tiltTarget.y
}

function onMouseUp() {
  if (!isDragging) return
  isDragging = false
  startSpring()
}

function onTouchStart(e: TouchEvent) {
  const t = e.touches[0]
  lastDragX = t.clientX
  lastDragY = t.clientY
  if (springId) { cancelAnimationFrame(springId); springId = null }
}

function onTouchMove(e: TouchEvent) {
  const t = e.touches[0]
  const dx = t.clientX - lastDragX
  const dy = t.clientY - lastDragY
  lastDragX = t.clientX
  lastDragY = t.clientY
  tiltTarget.y = Math.max(-9, Math.min(9, tiltTarget.y + dx * 0.04))
  tiltTarget.x = Math.max(-6, Math.min(6, tiltTarget.x - dy * 0.04))
  sceneTilt.x = tiltTarget.x
  sceneTilt.y = tiltTarget.y
}

function onTouchEnd() {
  startSpring()
}

const sceneStyle = computed(() => ({
  transform: `perspective(1100px) rotateX(${sceneTilt.x}deg) rotateY(${sceneTilt.y}deg)`,
}))

const titleStyle = computed(() => ({
  transform: `translate(${-sceneTilt.y * 3.5}px, ${sceneTilt.x * 2.5}px)`,
}))

// ── Per-card 3D tilt (key-based for dynamic cards) ───────────────
const cardTilts = reactive(
  new Map<string, { tx: number; ty: number; gx: number; gy: number; hover: boolean }>()
)

function getTilt(key: string) {
  if (!cardTilts.has(key)) {
    cardTilts.set(key, { tx: 0, ty: 0, gx: 50, gy: 50, hover: false })
  }
  return cardTilts.get(key)!
}

function onCardMove(e: PointerEvent, key: string) {
  const el = e.currentTarget as HTMLElement
  const r = el.getBoundingClientRect()
  const nx = ((e.clientX - r.left) / r.width) * 2 - 1
  const ny = ((e.clientY - r.top) / r.height) * 2 - 1
  const c = getTilt(key)
  c.tx = ny * -5
  c.ty = nx * 5
  c.gx = (nx + 1) * 50
  c.gy = (ny + 1) * 50
}

function onCardEnter(key: string) {
  getTilt(key).hover = true
}

function onCardLeave(key: string) {
  const c = getTilt(key)
  c.tx = 0
  c.ty = 0
  c.gx = 50
  c.gy = 50
  c.hover = false
}

function cardStyle(key: string) {
  const c = getTilt(key)
  return {
    transform: `perspective(600px) rotateX(${c.tx}deg) rotateY(${c.ty}deg)`,
    '--gx': `${c.gx}%`,
    '--gy': `${c.gy}%`,
    transition: c.hover
      ? 'box-shadow 0.2s ease'
      : 'transform 0.6s cubic-bezier(0.23, 1, 0.32, 1), box-shadow 0.2s ease',
  }
}

// ── Lifecycle ────────────────────────────────────────────────────
onMounted(async () => {
  window.addEventListener('mousedown', onMouseDown)
  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup', onMouseUp)
  window.addEventListener('touchstart', onTouchStart, { passive: true })
  window.addEventListener('touchmove', onTouchMove, { passive: true })
  window.addEventListener('touchend', onTouchEnd, { passive: true })
  await initCosmic()
})

onUnmounted(() => {
  if (springId) cancelAnimationFrame(springId)
  destroyCosmic()
  window.removeEventListener('mousedown', onMouseDown)
  window.removeEventListener('mousemove', onMouseMove)
  window.removeEventListener('mouseup', onMouseUp)
  window.removeEventListener('touchstart', onTouchStart)
  window.removeEventListener('touchmove', onTouchMove)
  window.removeEventListener('touchend', onTouchEnd)
  med.stop()
})
</script>

<template>
  <div class="home" @dragstart.prevent>
    <canvas ref="bgCanvas" class="home-bg" aria-hidden="true"></canvas>

    <div class="content-scene" :style="sceneStyle">
      <h1 class="title" :style="titleStyle">Channel Zero: Dreamer</h1>

      <!-- ── Stage: Home ── -->
      <Transition name="stage" mode="out-in">
        <div v-if="stage === 'home'" key="home" class="stage-content">
          <!-- Profile bar (returning user) -->
          <div v-if="token" class="profile-bar">
            <span class="profile-badge" :style="{ color: token.palette.accent }">
              {{ themeLabels[token.theme] }}
            </span>
            <span class="profile-arch">{{ token.archetype }}</span>
            <div class="profile-swatches">
              <span class="swatch-dot" :style="{ background: token.palette.primary }"></span>
              <span class="swatch-dot" :style="{ background: token.palette.accent }"></span>
            </div>
            <button class="profile-retake" @click="retakePoll">retake</button>
          </div>

          <!-- Featured card -->
          <div
            class="featured-card"
            :style="cardStyle('featured')"
            @pointermove="onCardMove($event, 'featured')"
            @pointerenter="onCardEnter('featured')"
            @pointerleave="onCardLeave('featured')"
            @click="handleFeaturedClick"
          >
            <span class="card-icon featured-icon">✦</span>
            <span class="card-title featured-title">{{ featuredTitle }}</span>
            <span class="card-desc">{{ featuredDesc }}</span>
            <span v-if="token && recommendedSession" class="rec-badge">Recommended</span>
            <div class="card-glare"></div>
          </div>

          <!-- Alt sessions (returning user) -->
          <div v-if="token" class="alt-sessions">
            <button
              v-for="s in otherSessions"
              :key="s.route"
              class="alt-session-btn"
              @click="router.push(s.route)"
            >
              <span class="alt-icon">{{ s.icon }}</span>
              {{ s.label }}
            </button>
          </div>

          <!-- Utility cards grid -->
          <div class="nav-grid">
            <router-link
              to="/checkin"
              class="nav-card nav-card--pipeline"
              :style="cardStyle('checkin')"
              @pointermove="onCardMove($event, 'checkin')"
              @pointerenter="onCardEnter('checkin')"
              @pointerleave="onCardLeave('checkin')"
            >
              <span class="card-icon">&#x2726;</span>
              <span class="card-title">Check-In</span>
              <span class="card-desc">Journal, intake, and the game — your daily pipeline</span>
              <div class="card-glare"></div>
            </router-link>

            <router-link
              to="/journal"
              class="nav-card"
              :style="cardStyle('journal')"
              @pointermove="onCardMove($event, 'journal')"
              @pointerenter="onCardEnter('journal')"
              @pointerleave="onCardLeave('journal')"
            >
              <span class="card-icon">&#x270D;</span>
              <span class="card-title">Journal</span>
              <span class="card-desc">Write, draw, record — reflective journaling with TTS</span>
              <div class="card-glare"></div>
            </router-link>

            <div
              class="nav-card nav-card--meditation"
              :style="cardStyle('meditation')"
              @pointermove="onCardMove($event, 'meditation')"
              @pointerenter="onCardEnter('meditation')"
              @pointerleave="onCardLeave('meditation')"
              @click="openMeditation"
            >
              <span class="card-icon">🧘</span>
              <span class="card-title">5-Min Meditation</span>
              <span class="card-desc">Guided affirmations with gentle music and nature sounds</span>
              <div class="card-glare"></div>
            </div>

            <router-link
              to="/reader"
              class="nav-card"
              :style="cardStyle('reader')"
              @pointermove="onCardMove($event, 'reader')"
              @pointerenter="onCardEnter('reader')"
              @pointerleave="onCardLeave('reader')"
            >
              <span class="card-icon">📖</span>
              <span class="card-title">Reader</span>
              <span class="card-desc">Speed-read through uploaded stories and text</span>
              <div class="card-glare"></div>
            </router-link>

            <router-link
              to="/audio"
              class="nav-card"
              :style="cardStyle('audio')"
              @pointermove="onCardMove($event, 'audio')"
              @pointerenter="onCardEnter('audio')"
              @pointerleave="onCardLeave('audio')"
            >
              <span class="card-icon">🎵</span>
              <span class="card-title">Audio</span>
              <span class="card-desc">Browse and play background audio tracks</span>
              <div class="card-glare"></div>
            </router-link>

            <router-link
              to="/glass"
              class="nav-card"
              :style="cardStyle('glass')"
              @pointermove="onCardMove($event, 'glass')"
              @pointerenter="onCardEnter('glass')"
              @pointerleave="onCardLeave('glass')"
            >
              <span class="card-icon">💧</span>
              <span class="card-title">Liquid Glass</span>
              <span class="card-desc">Interactive liquid glass visual playground</span>
              <div class="card-glare"></div>
            </router-link>
          </div>
        </div>

        <!-- ── Stage: Poll ── -->
        <div v-else-if="stage === 'poll'" key="poll" class="stage-content poll-section">
          <Transition
            :name="pollDirection === 'forward' ? 'slide-fwd' : 'slide-back'"
            mode="out-in"
          >
            <div :key="pollStep" class="poll-step">
              <div class="poll-progress">
                <div class="poll-progress-fill" :style="{ width: `${pollProgress * 100}%` }"></div>
              </div>

              <p class="poll-step-label">{{ pollStep }} / {{ questions.length }}</p>
              <p class="poll-question">{{ currentQuestion.text }}</p>

              <div class="poll-options">
                <button
                  v-for="opt in currentQuestion.options"
                  :key="opt.value"
                  :class="[
                    'poll-option',
                    { 'poll-option--selected': answers[currentQuestion.key] === opt.value },
                  ]"
                  @click="selectAnswer(opt.value)"
                >
                  <span class="option-label">{{ opt.label }}</span>
                  <span class="option-sublabel">{{ opt.sublabel }}</span>
                </button>
              </div>

              <button class="btn-ghost poll-back" @click="pollBack">
                ← {{ pollStep <= 1 ? 'Back to home' : 'Back' }}
              </button>
            </div>
          </Transition>
        </div>
      </Transition>
    </div>

    <!-- ── Meditation overlay ── -->
    <Teleport to="body">
      <Transition name="med-fade">
        <div v-if="showMeditation" class="meditation-overlay">
          <button class="med-close" @click="closeMeditation">×</button>

          <!-- Pre-start screen -->
          <div v-if="!med.isActive.value" class="med-center">
            <div class="med-intro">
              <span class="med-intro-icon">🧘</span>
              <h2 class="med-intro-title">5-Minute Meditation</h2>
              <p class="med-intro-desc">
                Gentle music, nature sounds, and guided affirmations<br />
                to help you settle into the present moment.
              </p>
              <button class="med-begin-btn" @click="med.start()">Begin</button>
            </div>
          </div>

          <!-- Active meditation -->
          <div v-else class="med-center">
            <Transition name="affirmation" mode="out-in">
              <p :key="med.affirmationKey.value" class="med-affirmation">
                {{ med.currentAffirmation.value }}
              </p>
            </Transition>

            <div class="med-ring-wrap">
              <svg class="med-ring" viewBox="0 0 120 120">
                <circle class="ring-track" cx="60" cy="60" r="52" />
                <circle
                  class="ring-progress"
                  cx="60"
                  cy="60"
                  r="52"
                  :stroke-dasharray="med.ringCircumference"
                  :stroke-dashoffset="med.ringOffset.value"
                />
              </svg>
              <span class="med-time">{{ med.formatTime(med.remaining.value) }}</span>
            </div>

            <p v-if="med.isComplete.value" class="med-complete">Session complete</p>
          </div>

          <!-- Controls -->
          <div v-if="med.isActive.value && !med.isComplete.value" class="med-controls">
            <button class="med-pause-btn" @click="med.togglePause()">
              {{ med.isPaused.value ? '▶' : '⏸' }}
            </button>

            <div class="volume-group">
              <label class="volume-label">Music</label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.01"
                class="volume-slider"
                :value="med.musicVolume.value"
                @input="med.setMusicVol(+($event.target! as any).value)"
              />
            </div>

            <div class="volume-group">
              <label class="volume-label">Nature</label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.01"
                class="volume-slider"
                :value="med.natureVolume.value"
                @input="med.setNatureVol(+($event.target! as any).value)"
              />
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
/* ── Layout ── */
.home {
  text-align: center;
  user-select: none;
  -webkit-user-select: none;
  position: relative;
  background: #08060e;
  min-height: calc(100vh - 3rem);
  padding-bottom: 2rem;
}

.home-bg {
  position: fixed;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 0;
}

.content-scene {
  will-change: transform;
  transform-origin: center center;
  position: relative;
  z-index: 1;
}

.title {
  font-size: 2rem;
  font-weight: bold;
  margin-bottom: 0.5rem;
  color: #e2e8f0;
  margin-top: 2rem;
  will-change: transform;
}

.stage-content {
  max-width: 600px;
  margin: 0 auto;
  padding: 0 1rem;
}

/* ── Stage transition ── */
.stage-enter-active,
.stage-leave-active {
  transition: all 0.3s ease;
}
.stage-enter-from {
  opacity: 0;
  transform: translateY(12px);
}
.stage-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* ── Profile bar ── */
.profile-bar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.6rem 1rem;
  margin-bottom: 1.25rem;
  background: rgba(30, 30, 50, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 0.6rem;
}

.profile-badge {
  font-size: 0.85rem;
  font-weight: 700;
  letter-spacing: 0.03em;
}

.profile-arch {
  font-size: 0.78rem;
  color: #94a3b8;
}

.profile-swatches {
  display: flex;
  gap: 0.3rem;
  margin-left: auto;
}

.swatch-dot {
  width: 0.75rem;
  height: 0.75rem;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.12);
}

.profile-retake {
  background: none;
  border: none;
  color: #475569;
  font-size: 0.7rem;
  font-family: inherit;
  cursor: pointer;
  padding: 0.2rem 0.4rem;
  transition: color 0.15s;
}

.profile-retake:hover {
  color: #94a3b8;
}

/* ── Featured card ── */
.featured-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 2.5rem 2rem;
  margin-bottom: 1rem;
  background: linear-gradient(135deg, rgba(30, 20, 60, 0.9), rgba(20, 20, 50, 0.85));
  border: 1px solid rgba(99, 102, 241, 0.3);
  border-radius: 1rem;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  will-change: transform;
  text-decoration: none;
  color: #e2e8f0;
}

.featured-card:hover {
  border-color: rgba(167, 139, 250, 0.6);
  box-shadow: 0 12px 48px rgba(99, 102, 241, 0.2);
}

.featured-icon {
  font-size: 2rem;
  color: #a78bfa;
}

.featured-title {
  font-size: 1.3rem;
  font-weight: 600;
  background: linear-gradient(135deg, #c4b5fd, #818cf8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.rec-badge {
  font-size: 0.6rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #a78bfa;
  font-weight: 600;
}

/* ── Alt session buttons ── */
.alt-sessions {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.25rem;
  justify-content: center;
  flex-wrap: wrap;
}

.alt-session-btn {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.45rem 0.85rem;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 0.5rem;
  color: #94a3b8;
  font-size: 0.78rem;
  font-family: inherit;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}

.alt-session-btn:hover {
  background: rgba(99, 102, 241, 0.12);
  border-color: rgba(99, 102, 241, 0.35);
  color: #e2e8f0;
}

.alt-icon {
  font-size: 0.9rem;
}

/* ── Card grid ── */
.nav-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.25rem;
}

.nav-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 2rem 1.5rem;
  background: rgba(30, 30, 50, 0.8);
  border: 1px solid rgba(100, 100, 255, 0.15);
  border-radius: 1rem;
  text-decoration: none;
  color: #e2e8f0;
  position: relative;
  overflow: hidden;
  will-change: transform;
  cursor: pointer;
}

.nav-card:hover {
  background: rgba(40, 40, 70, 0.9);
  border-color: rgba(99, 102, 241, 0.5);
  box-shadow: 0 12px 36px rgba(0, 0, 0, 0.45);
}

.nav-card--pipeline {
  border-color: rgba(99, 102, 241, 0.3);
  background: linear-gradient(135deg, rgba(30, 20, 60, 0.85), rgba(20, 20, 50, 0.8));
}

.nav-card--pipeline:hover {
  border-color: rgba(167, 139, 250, 0.6);
  box-shadow: 0 12px 36px rgba(99, 102, 241, 0.15);
}

.nav-card--meditation {
  border-color: rgba(217, 119, 6, 0.2);
}

.nav-card--meditation:hover {
  border-color: rgba(217, 119, 6, 0.45);
  box-shadow: 0 12px 36px rgba(217, 119, 6, 0.1);
}

.card-icon {
  font-size: 2.5rem;
}

.card-title {
  font-size: 1.1rem;
  font-weight: 600;
}

.card-desc {
  font-size: 0.8rem;
  color: #94a3b8;
  line-height: 1.4;
}

.card-glare {
  position: absolute;
  inset: 0;
  pointer-events: none;
  border-radius: inherit;
  background: radial-gradient(
    circle at var(--gx, 50%) var(--gy, 50%),
    rgba(255, 255, 255, 0.13),
    transparent 62%
  );
  opacity: 0;
  transition: opacity 0.3s ease;
}

.nav-card:hover .card-glare,
.featured-card:hover .card-glare {
  opacity: 1;
}

/* ── Poll section ── */
.poll-section {
  max-width: 600px;
  background: rgba(20, 20, 40, 0.85);
  border: 1px solid rgba(100, 100, 255, 0.18);
  border-radius: 1rem;
  padding: 2.5rem 2rem;
  backdrop-filter: blur(12px);
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.5);
}

.poll-progress {
  height: 2px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 1px;
  margin-bottom: 1.5rem;
  overflow: hidden;
}

.poll-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #6366f1, #a78bfa);
  border-radius: 1px;
  transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.poll-step-label {
  font-size: 0.7rem;
  color: #64748b;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  margin: 0 0 1.25rem;
}

.poll-question {
  font-size: 1.05rem;
  color: #e2e8f0;
  line-height: 1.65;
  margin: 0 0 2rem;
  text-align: left;
}

.poll-options {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.poll-option {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.2rem;
  padding: 1rem 1.25rem;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 0.6rem;
  color: #e2e8f0;
  cursor: pointer;
  font-family: inherit;
  text-align: left;
  transition: background 0.15s, border-color 0.15s, transform 0.1s;
  width: 100%;
}

.poll-option:hover {
  background: rgba(99, 102, 241, 0.12);
  border-color: rgba(99, 102, 241, 0.35);
  transform: translateX(2px);
}

.poll-option--selected {
  background: rgba(99, 102, 241, 0.2);
  border-color: rgba(99, 102, 241, 0.6);
}

.option-label {
  font-size: 0.95rem;
  font-weight: 500;
}

.option-sublabel {
  font-size: 0.78rem;
  color: #94a3b8;
}

.btn-ghost {
  background: none;
  border: none;
  color: #64748b;
  font-size: 0.8rem;
  font-family: inherit;
  cursor: pointer;
  padding: 0.4rem 0;
  transition: color 0.15s;
}

.btn-ghost:hover {
  color: #94a3b8;
}

.poll-back {
  display: block;
}

/* Poll transitions */
.slide-fwd-enter-active,
.slide-fwd-leave-active,
.slide-back-enter-active,
.slide-back-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-fwd-enter-from {
  opacity: 0;
  transform: translateX(28px);
}
.slide-fwd-leave-to {
  opacity: 0;
  transform: translateX(-28px);
}

.slide-back-enter-from {
  opacity: 0;
  transform: translateX(-28px);
}
.slide-back-leave-to {
  opacity: 0;
  transform: translateX(28px);
}

/* ── Meditation overlay ── */
.meditation-overlay {
  position: fixed;
  inset: 0;
  z-index: 2000;
  background: rgba(5, 5, 15, 0.97);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.med-fade-enter-active,
.med-fade-leave-active {
  transition: opacity 0.5s ease;
}
.med-fade-enter-from,
.med-fade-leave-to {
  opacity: 0;
}

.med-close {
  position: absolute;
  top: 1rem;
  right: 1.25rem;
  background: none;
  border: none;
  color: #475569;
  font-size: 1.8rem;
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  line-height: 1;
  transition: color 0.15s;
  z-index: 1;
}

.med-close:hover {
  color: #94a3b8;
}

.med-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2rem;
  padding: 0 2rem;
  max-width: 500px;
  text-align: center;
  flex: 1;
  justify-content: center;
}

/* Pre-start intro */
.med-intro {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.med-intro-icon {
  font-size: 3rem;
}

.med-intro-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #e2e8f0;
  margin: 0;
}

.med-intro-desc {
  font-size: 0.9rem;
  color: #94a3b8;
  line-height: 1.65;
  margin: 0;
}

.med-begin-btn {
  padding: 0.85rem 2.5rem;
  background: linear-gradient(135deg, rgba(217, 119, 6, 0.2), rgba(167, 139, 250, 0.15));
  border: 1px solid rgba(217, 119, 6, 0.35);
  border-radius: 0.6rem;
  color: #fbbf24;
  font-size: 1rem;
  font-weight: 600;
  font-family: inherit;
  letter-spacing: 0.04em;
  cursor: pointer;
  transition: background 0.2s, border-color 0.2s, box-shadow 0.2s;
  margin-top: 0.5rem;
}

.med-begin-btn:hover {
  background: linear-gradient(135deg, rgba(217, 119, 6, 0.35), rgba(167, 139, 250, 0.25));
  border-color: rgba(251, 191, 36, 0.5);
  box-shadow: 0 0 28px rgba(217, 119, 6, 0.15);
}

/* Affirmation */
.med-affirmation {
  font-size: 1.25rem;
  color: #e2e8f0;
  line-height: 1.7;
  max-width: 420px;
  min-height: 3.5rem;
  margin: 0;
}

.affirmation-enter-active,
.affirmation-leave-active {
  transition: opacity 1.2s ease;
}
.affirmation-enter-from,
.affirmation-leave-to {
  opacity: 0;
}

/* Progress ring */
.med-ring-wrap {
  position: relative;
  width: 120px;
  height: 120px;
}

.med-ring {
  width: 120px;
  height: 120px;
  transform: rotate(-90deg);
}

.ring-track {
  fill: none;
  stroke: rgba(255, 255, 255, 0.06);
  stroke-width: 3;
}

.ring-progress {
  fill: none;
  stroke: rgba(167, 139, 250, 0.5);
  stroke-width: 3;
  stroke-linecap: round;
  transition: stroke-dashoffset 0.5s ease;
}

.med-time {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
  color: #94a3b8;
  font-variant-numeric: tabular-nums;
}

.med-complete {
  font-size: 0.9rem;
  color: #a78bfa;
  font-weight: 500;
}

/* Controls */
.med-controls {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  padding: 1.5rem 2rem;
  flex-wrap: wrap;
  justify-content: center;
}

.med-pause-btn {
  width: 2.75rem;
  height: 2.75rem;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #e2e8f0;
  font-size: 1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s, border-color 0.15s;
  flex-shrink: 0;
}

.med-pause-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.25);
}

.volume-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.volume-label {
  font-size: 0.7rem;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  min-width: 3rem;
}

.volume-slider {
  -webkit-appearance: none;
  appearance: none;
  width: 80px;
  height: 3px;
  background: rgba(255, 255, 255, 0.12);
  border-radius: 2px;
  outline: none;
}

.volume-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #94a3b8;
  cursor: pointer;
  border: none;
  transition: background 0.15s;
}

.volume-slider::-webkit-slider-thumb:hover {
  background: #e2e8f0;
}

.volume-slider::-moz-range-thumb {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #94a3b8;
  cursor: pointer;
  border: none;
}

/* ── Mobile ── */
@media (max-width: 480px) {
  .nav-grid {
    grid-template-columns: 1fr;
  }

  .poll-section {
    padding: 1.75rem 1.25rem;
  }

  .poll-question {
    font-size: 0.95rem;
  }

  .poll-option {
    padding: 0.85rem 1rem;
  }

  .med-affirmation {
    font-size: 1.1rem;
    padding: 0 1rem;
  }

  .med-controls {
    gap: 1rem;
    padding: 1rem;
  }

  .volume-slider {
    width: 60px;
  }
}
</style>
