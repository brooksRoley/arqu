<script setup lang="ts">
import { ref, computed, nextTick, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/composables/useAuthStore'
import { usePollStore } from '@/composables/usePollStore'
import { useVibeStore } from '@/composables/useVibeStore'

const router = useRouter()
const route = useRoute()
const { isAuthenticated, user } = useAuthStore()
const { token: pollToken } = usePollStore()
const { markConnected } = useVibeStore()

if (!isAuthenticated.value) {
  router.replace('/login')
}

const accent = computed(() => pollToken.value?.palette?.accent || '#a78bfa')
const theme = computed(() => pollToken.value?.theme || 'liminal')
const archetype = computed(() => pollToken.value?.archetype || 'the wanderer')

// ── Game State ────────────────────────────────────────────────────

type GamePhase = 'lobby' | 'scanning' | 'matched' | 'deployed'

const phase = ref<GamePhase>('lobby')
const scanProgress = ref(0)
const currentStatus = ref('')

const matchProfile = ref<{
  codename: string
  compatibility: number
  venue: string
  window: string
  sonicOverlap: string
  neuroticFootprint: string
  logistics: string
} | null>(null)

const statusMessages = [
  'Scanning vibe vectors...',
  'Cross-referencing attachment matrices...',
  'Calculating optimal deployment windows...',
  'Identifying compatible signal patterns...',
  'Triangulating Thursday-Saturday availability...',
  'Locking coordinates...',
]

// ── Oracle debrief chat ───────────────────────────────────────────

interface OracleMsg {
  id: number
  role: 'user' | 'oracle'
  text: string
}

const oracleLog = ref<OracleMsg[]>([])
const oracleInput = ref('')
const oracleEl = ref<HTMLElement | null>(null)

function generateOracleDebrief(): string {
  if (!matchProfile.value) return ''
  return `Nightly batch processed. You matched with ${matchProfile.value.codename} at ${matchProfile.value.compatibility}%. What are your initial thoughts on their matrix?`
}

const oracleResponses = [
  () => {
    const m = matchProfile.value!
    return `The LLM parsed their signal. They use melancholy audio to self-regulate, but their social interactions are highly assertive. This complements your ${archetype.value} pattern — they pick the venue, you set the tone.`
  },
  () => {
    const m = matchProfile.value!
    return `If you look at the calendar overlap, ${m.window} is your only clean window. The algorithm suggests they are emotionally guarded but physically available. Do you want me to draft the opening approach based on your shared frequency profile?`
  },
  () => `Your hesitation is noted and expected. The vibe vector accounts for approach anxiety — it's already factored into the compatibility score. The question isn't whether you're ready. The question is whether you'll let the data be smarter than your doubt.`,
  () => `I've seen your journal entries. You write about wanting connection while systematically avoiding it. This match is the algorithm calling your bluff. The rest is up to you.`,
]

let oracleResponseIdx = 0

async function sendToOracle() {
  const text = oracleInput.value.trim()
  if (!text) return

  oracleLog.value.push({ id: Date.now(), role: 'user', text })
  oracleInput.value = ''
  await scrollOracle()

  await new Promise((r) => setTimeout(r, 600 + Math.random() * 500))

  const responseFn = oracleResponses[Math.min(oracleResponseIdx, oracleResponses.length - 1)]
  oracleLog.value.push({ id: Date.now() + 1, role: 'oracle', text: responseFn() })
  oracleResponseIdx++
  await scrollOracle()
}

async function scrollOracle() {
  await nextTick()
  if (oracleEl.value) oracleEl.value.scrollTop = oracleEl.value.scrollHeight
}

// ── Scan + Match ──────────────────────────────────────────────────

async function startScan() {
  phase.value = 'scanning'
  scanProgress.value = 0

  for (let i = 0; i < statusMessages.length; i++) {
    currentStatus.value = statusMessages[i]
    scanProgress.value = Math.round(((i + 1) / statusMessages.length) * 100)
    await delay(700 + Math.random() * 500)
  }

  matchProfile.value = generateMatch()
  oracleLog.value = [{ id: 1, role: 'oracle', text: generateOracleDebrief() }]
  phase.value = 'matched'
}

function generateMatch() {
  const codenames = [
    'Signal Ghost', 'Warm Static', 'Night Architecture',
    'Soft Collision', 'Parallel Drift', 'Velvet Algorithm',
    'Midnight Frequency', 'Quiet Voltage',
  ]
  const venues = [
    'a rooftop bar with low amber lighting',
    'a gallery opening in the warehouse district',
    'a listening lounge playing ambient sets',
    'a late-night bookstore with wine',
    'a speakeasy behind a coffee shop',
    'a night market under string lights',
  ]
  const windows = ['Thursday 8PM', 'Friday 9PM', 'Saturday 7PM', 'Friday 10PM', 'Saturday 9PM']

  const sonicOverlaps = [
    'You both hyper-fixate on aggressive 90s shoegaze and high-tempo ambient. Their valence is similarly depressive.',
    'Shared rotation: slow-burn post-rock and downtempo electronic. Emotional bandwidth overlaps in the 60-80 BPM range.',
    'Heavy overlap in dark ambient and minimal techno. You both use music as a regulation tool, not entertainment.',
  ]
  const neuroticPrints = [
    'Match shows high linguistic dominance and dark humor. Algorithm suggests they pay for the first round.',
    'Their social footprint is guarded but consistent — long gaps between posts, then bursts of vulnerability. Mirror pattern to yours.',
    'High analytical drive, low impulsivity. They will overthink the date too. At least you will overthink it together.',
  ]

  const v = venues[Math.floor(Math.random() * venues.length)]
  const w = windows[Math.floor(Math.random() * windows.length)]

  return {
    codename: codenames[Math.floor(Math.random() * codenames.length)],
    compatibility: 72 + Math.floor(Math.random() * 26),
    venue: v,
    window: w,
    sonicOverlap: sonicOverlaps[Math.floor(Math.random() * sonicOverlaps.length)],
    neuroticFootprint: neuroticPrints[Math.floor(Math.random() * neuroticPrints.length)],
    logistics: `Neon DB queries confirm you both have ${w.split(' ')[0]} open. ${v.charAt(0).toUpperCase() + v.slice(1)} is suggested — 3 miles away.`,
  }
}

function initiateContact() {
  phase.value = 'deployed'
}

function goBack() {
  router.push('/checkin')
}

function delay(ms: number) {
  return new Promise((r) => setTimeout(r, ms))
}

onMounted(() => {
  // Spotify OAuth callback lands here with ?spotify=connected
  if (route.query.spotify === 'connected') {
    markConnected('spotify')
    router.replace({ path: '/game' })
  }

  if (pollToken.value) {
    setTimeout(() => startScan(), 600)
  }
})
</script>

<template>
  <div class="game-wrap">
    <!-- Header -->
    <header class="game-header">
      <button class="back-btn" @click="goBack">← Back</button>
      <h1 class="game-title">Nightly Yield</h1>
      <p class="game-subtitle">Deployment protocol</p>
    </header>

    <!-- Lobby -->
    <div v-if="phase === 'lobby'" class="phase-center">
      <div class="lobby-hero">
        <span class="hero-icon">&#x2726;</span>
        <p class="hero-text">
          Your psychoanalytic profile has been loaded.<br />
          Ready to enter the matching engine?
        </p>
        <button class="action-btn" :style="{ background: accent }" @click="startScan">
          Initialize Scan
        </button>
      </div>
    </div>

    <!-- Scanning -->
    <div v-if="phase === 'scanning'" class="phase-center">
      <div class="scan-display">
        <div class="scan-ring">
          <svg viewBox="0 0 100 100" class="ring-svg">
            <circle cx="50" cy="50" r="44" class="ring-track" />
            <circle
              cx="50" cy="50" r="44"
              class="ring-fill"
              :style="{ stroke: accent, strokeDasharray: 276.46, strokeDashoffset: 276.46 * (1 - scanProgress / 100) }"
            />
          </svg>
          <span class="scan-percent">{{ scanProgress }}%</span>
        </div>
        <p class="scan-status">{{ currentStatus }}</p>
      </div>
    </div>

    <!-- Matched — split panel -->
    <div v-if="phase === 'matched' && matchProfile" class="split-panel">
      <!-- Left: Match card -->
      <div class="match-panel">
        <div class="match-card">
          <div class="match-top">
            <div class="match-accent-bar" :style="{ background: accent }" />
            <div class="match-identity">
              <h2 class="match-codename" :style="{ color: accent }">{{ matchProfile.codename }}</h2>
              <span class="match-compat">{{ matchProfile.compatibility }}% Vibe Alignment</span>
            </div>
            <button class="contact-btn" :style="{ background: accent }" @click="initiateContact">
              Initiate Contact
            </button>
          </div>

          <div class="match-breakdown">
            <div class="breakdown-item">
              <span class="breakdown-label">Sonic Overlap</span>
              <p class="breakdown-text">{{ matchProfile.sonicOverlap }}</p>
            </div>
            <div class="breakdown-item">
              <span class="breakdown-label">Neurotic Footprint</span>
              <p class="breakdown-text">{{ matchProfile.neuroticFootprint }}</p>
            </div>
            <div class="breakdown-item">
              <span class="breakdown-label">Logistics</span>
              <p class="breakdown-text">{{ matchProfile.logistics }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Oracle debrief chat -->
      <div class="oracle-panel">
        <div class="oracle-header">
          <span class="oracle-dot" />
          <span class="oracle-title">Vibe Oracle</span>
          <span class="oracle-hint">Process your results before speaking to them.</span>
        </div>

        <div ref="oracleEl" class="oracle-thread">
          <div
            v-for="msg in oracleLog"
            :key="msg.id"
            :class="['oracle-msg', `oracle-msg--${msg.role}`]"
          >
            <span class="oracle-msg-label">{{ msg.role === 'user' ? 'You' : 'Oracle' }}</span>
            <p class="oracle-msg-bubble">{{ msg.text }}</p>
          </div>
        </div>

        <div class="oracle-input-row">
          <input
            v-model="oracleInput"
            type="text"
            class="oracle-input"
            placeholder="Why did it match me with them?"
            @keyup.enter="sendToOracle"
          />
        </div>
      </div>
    </div>

    <!-- Deployed -->
    <div v-if="phase === 'deployed'" class="phase-center">
      <div class="deployed-display">
        <span class="deployed-icon" :style="{ color: accent }">&#x2714;</span>
        <h2 class="deployed-title">Deployed</h2>
        <p class="deployed-text">
          Your coordinates have been locked. The vector is live.<br />
          Show up as yourself — the profile did the rest.
        </p>
        <div v-if="matchProfile" class="deployed-meta">
          {{ matchProfile.window }} &middot; {{ matchProfile.venue }}
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.game-wrap {
  min-height: calc(100vh - 3rem);
  display: flex;
  flex-direction: column;
  padding: 2rem 1.5rem 4rem;
  max-width: 1100px;
  margin: 0 auto;
}

/* ── Header ── */
.game-header {
  text-align: center;
  position: relative;
  margin-bottom: 2rem;
}

.back-btn {
  position: absolute;
  left: 0;
  top: 0.25rem;
  background: none;
  border: none;
  color: #64748b;
  font-size: 0.78rem;
  font-family: inherit;
  cursor: pointer;
  padding: 0.3rem 0;
  transition: color 0.15s;
}
.back-btn:hover { color: #94a3b8; }

.game-title {
  font-size: 1.5rem;
  font-weight: 800;
  color: #e2e8f0;
  margin: 0;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.game-subtitle {
  font-size: 0.7rem;
  color: #475569;
  margin: 0.2rem 0 0;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.phase-center {
  display: flex;
  justify-content: center;
  flex: 1;
  align-items: flex-start;
}

/* ── Lobby ── */
.lobby-hero {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.25rem;
  padding: 3rem 2rem;
  background: rgba(20, 20, 40, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 0.75rem;
  width: 100%;
  max-width: 500px;
  text-align: center;
}

.hero-icon { font-size: 3rem; color: #64748b; }

.hero-text {
  font-size: 0.9rem;
  color: #94a3b8;
  line-height: 1.65;
  margin: 0;
}

.action-btn, .contact-btn {
  padding: 0.6rem 1.5rem;
  border: none;
  border-radius: 0.4rem;
  color: #0f0f1a;
  font-size: 0.82rem;
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
  transition: opacity 0.15s, transform 0.1s;
}
.action-btn:hover, .contact-btn:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

/* ── Scanning ── */
.scan-display {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
  padding: 3rem 2rem;
}

.scan-ring { position: relative; width: 120px; height: 120px; }

.ring-svg { width: 100%; height: 100%; transform: rotate(-90deg); }

.ring-track {
  fill: none;
  stroke: rgba(255, 255, 255, 0.06);
  stroke-width: 3;
}

.ring-fill {
  fill: none;
  stroke-width: 3;
  stroke-linecap: round;
  transition: stroke-dashoffset 0.4s ease;
}

.scan-percent {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  color: #e2e8f0;
  font-variant-numeric: tabular-nums;
}

.scan-status {
  font-size: 0.82rem;
  color: #64748b;
  margin: 0;
  font-style: italic;
}

/* ── Split panel (match + oracle) ── */
.split-panel {
  display: flex;
  gap: 1.25rem;
  flex: 1;
  min-height: 0;
}

.match-panel { flex: 1; min-width: 0; }
.oracle-panel {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  background: rgba(10, 10, 25, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 0.75rem;
  overflow: hidden;
}

/* ── Match card ── */
.match-card {
  background: rgba(20, 20, 40, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 0.75rem;
  overflow: hidden;
}

.match-top {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1.25rem;
  position: relative;
}

.match-accent-bar {
  position: absolute;
  left: 0;
  top: 0;
  width: 3px;
  height: 100%;
}

.match-identity {
  flex: 1;
  padding-left: 0.5rem;
}

.match-codename {
  font-size: 1.25rem;
  font-weight: 700;
  margin: 0;
}

.match-compat {
  font-size: 0.72rem;
  color: #64748b;
}

.match-breakdown {
  padding: 0 1.25rem 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.breakdown-item {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.breakdown-label {
  font-size: 0.6rem;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: #64748b;
  font-weight: 600;
}

.breakdown-text {
  font-size: 0.8rem;
  color: #94a3b8;
  line-height: 1.55;
  margin: 0;
}

/* ── Oracle panel ── */
.oracle-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.85rem 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(5, 5, 15, 0.5);
  flex-wrap: wrap;
}

.oracle-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #22c55e;
  flex-shrink: 0;
}

.oracle-title {
  font-size: 0.88rem;
  font-weight: 600;
  color: #e2e8f0;
}

.oracle-hint {
  font-size: 0.65rem;
  color: #475569;
  width: 100%;
}

.oracle-thread {
  flex: 1;
  overflow-y: auto;
  padding: 0.85rem;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  font-family: monospace;
  font-size: 0.8rem;
}

.oracle-thread::-webkit-scrollbar { width: 4px; }
.oracle-thread::-webkit-scrollbar-track { background: transparent; }
.oracle-thread::-webkit-scrollbar-thumb { background: #374151; border-radius: 4px; }

.oracle-msg { max-width: 88%; }
.oracle-msg--user { align-self: flex-end; text-align: right; }
.oracle-msg--oracle { align-self: flex-start; }

.oracle-msg-label {
  font-size: 0.55rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #475569;
  display: block;
  margin-bottom: 0.15rem;
}

.oracle-msg-bubble {
  margin: 0;
  padding: 0.6rem 0.75rem;
  border-radius: 0.5rem;
  line-height: 1.55;
}

.oracle-msg--user .oracle-msg-bubble {
  background: rgba(59, 130, 246, 0.12);
  border: 1px solid rgba(59, 130, 246, 0.2);
  color: #93c5fd;
}

.oracle-msg--oracle .oracle-msg-bubble {
  background: rgba(139, 92, 246, 0.08);
  border: 1px solid rgba(139, 92, 246, 0.15);
  color: #c4b5fd;
}

.oracle-input-row {
  padding: 0.75rem;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.oracle-input {
  width: 100%;
  background: rgba(0, 0, 0, 0.35);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 0.4rem;
  padding: 0.6rem 0.75rem;
  font-family: inherit;
  font-size: 0.82rem;
  color: #e2e8f0;
  outline: none;
  transition: border-color 0.15s;
  box-sizing: border-box;
}

.oracle-input:focus { border-color: rgba(139, 92, 246, 0.4); }
.oracle-input::placeholder { color: #475569; }

/* ── Deployed ── */
.deployed-display {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 3rem 2rem;
  text-align: center;
  max-width: 500px;
}

.deployed-icon { font-size: 3rem; }

.deployed-title {
  font-size: 1.3rem;
  font-weight: 700;
  color: #e2e8f0;
  margin: 0;
}

.deployed-text {
  font-size: 0.88rem;
  color: #94a3b8;
  line-height: 1.65;
  margin: 0;
}

.deployed-meta {
  font-size: 0.78rem;
  color: #64748b;
  margin-top: 0.5rem;
}

/* ── Mobile: stack panels ── */
@media (max-width: 768px) {
  .game-wrap { padding: 1.5rem 0.75rem 3rem; }

  .split-panel {
    flex-direction: column;
  }

  .oracle-panel {
    height: 400px;
  }
}
</style>
