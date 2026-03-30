<template>
  <div class="min-h-screen bg-black text-lime-400 p-6 lg:p-10 font-mono">
    <header class="mb-10 border-b border-lime-800 pb-4 flex items-baseline justify-between gap-4">
      <div>
        <h1 class="text-2xl lg:text-3xl font-bold tracking-tighter uppercase">Psychological Profile</h1>
        <p class="text-lime-600 mt-1 text-xs tracking-widest uppercase">The architecture of your resonance</p>
      </div>
      <div v-if="oauthState" class="flex flex-wrap gap-2 justify-end">
        <span
          v-for="p in connectedProviders"
          :key="p"
          class="text-[9px] uppercase tracking-widest border border-lime-800 px-2 py-0.5 text-lime-600"
        >{{ p }}</span>
      </div>
    </header>

    <!-- ── Assessment Form ──────────────────────────────────────── -->
    <div v-if="!profile && !loading" class="max-w-2xl mx-auto">
      <!-- Progress bar -->
      <div class="mb-8">
        <div class="flex justify-between mb-2 text-[10px] text-lime-700 uppercase tracking-widest">
          <span>{{ STEP_LABELS[step] }}</span>
          <span>{{ step + 1 }} / {{ STEP_LABELS.length }}</span>
        </div>
        <div class="h-px bg-lime-900">
          <div class="h-px bg-lime-500 transition-all duration-500" :style="{ width: `${(step / (STEP_LABELS.length - 1)) * 100}%` }" />
        </div>
      </div>

      <!-- Step 0 — OCEAN (Big Five) -------------------------------- -->
      <div v-if="step === 0" class="space-y-8">
        <p class="text-xs text-lime-600 italic">Rate how accurately each statement describes you. 1 = Not at all · 5 = Very much</p>
        <div v-for="(item, i) in OCEAN_ITEMS" :key="i" class="space-y-2">
          <p class="text-sm text-lime-300">{{ item.text }}</p>
          <div class="flex gap-3">
            <button
              v-for="n in 5"
              :key="n"
              :class="[
                'w-9 h-9 border text-xs transition-all',
                oceanAnswers[i] === n
                  ? 'border-lime-400 bg-lime-900/60 text-lime-200'
                  : 'border-lime-900 text-lime-700 hover:border-lime-600 hover:text-lime-400'
              ]"
              @click="oceanAnswers[i] = n"
            >{{ n }}</button>
          </div>
        </div>
        <button
          :disabled="!oceanComplete"
          class="w-full border border-lime-600 p-3 text-xs uppercase tracking-widest transition-all disabled:opacity-30 disabled:cursor-not-allowed hover:bg-lime-900/40"
          @click="step++"
        >Continue →</button>
      </div>

      <!-- Step 1 — Attachment (ECR-R short form) ------------------ -->
      <div v-if="step === 1" class="space-y-8">
        <p class="text-xs text-lime-600 italic">Rate how much each statement describes your feelings in close relationships. 1 = Disagree strongly · 7 = Agree strongly</p>
        <div v-for="(item, i) in ATTACHMENT_ITEMS" :key="i" class="space-y-2">
          <p class="text-sm text-lime-300">{{ item.text }}</p>
          <div class="flex gap-2">
            <button
              v-for="n in 7"
              :key="n"
              :class="[
                'w-9 h-9 border text-xs transition-all',
                attachAnswers[i] === n
                  ? 'border-lime-400 bg-lime-900/60 text-lime-200'
                  : 'border-lime-900 text-lime-700 hover:border-lime-600 hover:text-lime-400'
              ]"
              @click="attachAnswers[i] = n"
            >{{ n }}</button>
          </div>
        </div>
        <div class="flex gap-3">
          <button class="flex-1 border border-lime-900 p-3 text-xs uppercase tracking-widest hover:bg-lime-900/20" @click="step--">← Back</button>
          <button
            :disabled="!attachmentComplete"
            class="flex-1 border border-lime-600 p-3 text-xs uppercase tracking-widest transition-all disabled:opacity-30 disabled:cursor-not-allowed hover:bg-lime-900/40"
            @click="step++"
          >Continue →</button>
        </div>
      </div>

      <!-- Step 2 — Identity --------------------------------------- -->
      <div v-if="step === 2" class="space-y-6">
        <p class="text-xs text-lime-600 italic">Three signals that refine your compatibility coordinates.</p>

        <div>
          <label class="block mb-2 text-xs text-lime-600 uppercase tracking-wider">Primary Love Language</label>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <button
              v-for="ll in LOVE_LANGUAGES"
              :key="ll"
              :class="[
                'p-3 border text-left text-xs transition-all',
                form.love_language === ll
                  ? 'border-lime-400 bg-lime-900/50 text-lime-200'
                  : 'border-lime-900 text-lime-600 hover:border-lime-700 hover:text-lime-400'
              ]"
              @click="form.love_language = ll"
            >{{ ll }}</button>
          </div>
        </div>

        <div>
          <label class="block mb-2 text-xs text-lime-600 uppercase tracking-wider">Values Cluster</label>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <button
              v-for="vc in VALUES_CLUSTERS"
              :key="vc"
              :class="[
                'p-3 border text-left text-xs transition-all',
                form.values_cluster === vc
                  ? 'border-lime-400 bg-lime-900/50 text-lime-200'
                  : 'border-lime-900 text-lime-600 hover:border-lime-700 hover:text-lime-400'
              ]"
              @click="form.values_cluster = vc"
            >{{ vc }}</button>
          </div>
        </div>

        <div>
          <label class="block mb-2 text-xs text-lime-600 uppercase tracking-wider">Sociosexual Orientation</label>
          <div class="grid grid-cols-3 gap-2">
            <button
              v-for="so in SOCIOSEXUAL_OPTIONS"
              :key="so.value"
              :class="[
                'p-3 border text-xs transition-all',
                form.sociosexual === so.value
                  ? 'border-lime-400 bg-lime-900/50 text-lime-200'
                  : 'border-lime-900 text-lime-600 hover:border-lime-700 hover:text-lime-400'
              ]"
              @click="form.sociosexual = so.value"
            >
              <div class="font-semibold">{{ so.label }}</div>
              <div class="text-[9px] mt-0.5 opacity-70">{{ so.sub }}</div>
            </button>
          </div>
        </div>

        <div class="flex gap-3 pt-2">
          <button class="flex-1 border border-lime-900 p-3 text-xs uppercase tracking-widest hover:bg-lime-900/20" @click="step--">← Back</button>
          <button
            :disabled="!identityComplete"
            class="flex-1 border border-lime-600 p-3 text-xs uppercase tracking-widest transition-all disabled:opacity-30 disabled:cursor-not-allowed hover:bg-lime-900/40"
            @click="submitAssessment"
          >{{ submitting ? 'Synchronizing...' : 'Initialize Sync' }}</button>
        </div>
      </div>
    </div>

    <!-- ── Loading ─────────────────────────────────────────────── -->
    <div v-else-if="loading" class="flex items-center justify-center py-32">
      <div class="text-center space-y-3">
        <div class="w-px h-12 bg-lime-800 mx-auto animate-pulse" />
        <p class="text-xs text-lime-700 uppercase tracking-widest">Loading profile...</p>
      </div>
    </div>

    <!-- ── Dashboard ───────────────────────────────────────────── -->
    <div v-else-if="profile" class="grid grid-cols-1 lg:grid-cols-2 gap-8">

      <!-- Left column -->
      <div class="space-y-8">

        <!-- OCEAN Radar -->
        <section class="border border-lime-800 p-6 bg-black/30">
          <h2 class="text-lg mb-4 text-white uppercase tracking-widest text-center">OCEAN Signature</h2>
          <div class="flex justify-center py-4">
            <svg width="240" height="240" viewBox="0 0 200 200" class="overflow-visible">
              <polygon points="100,20 176,75 147,164 53,164 24,75" fill="none" stroke="#1a2e1a" stroke-width="1"/>
              <polygon points="100,60 138,87 123,132 77,132 62,87" fill="none" stroke="#1a2e1a" stroke-width="1"/>
              <line x1="100" y1="100" x2="100" y2="20" stroke="#1a2e1a"/>
              <line x1="100" y1="100" x2="176" y2="75" stroke="#1a2e1a"/>
              <line x1="100" y1="100" x2="147" y2="164" stroke="#1a2e1a"/>
              <line x1="100" y1="100" x2="53" y2="164" stroke="#1a2e1a"/>
              <line x1="100" y1="100" x2="24" y2="75" stroke="#1a2e1a"/>
              <polygon :points="radarPoints" fill="rgba(163,230,53,0.18)" stroke="#a3e635" stroke-width="1.5"/>
              <!-- Axis labels positioned outside the pentagon -->
              <text x="100" y="10" fill="#4d7c0f" font-size="7" text-anchor="middle" class="uppercase">Openness</text>
              <text x="186" y="78" fill="#4d7c0f" font-size="7" text-anchor="start" class="uppercase">Consci.</text>
              <text x="155" y="178" fill="#4d7c0f" font-size="7" text-anchor="middle" class="uppercase">Extra.</text>
              <text x="45" y="178" fill="#4d7c0f" font-size="7" text-anchor="middle" class="uppercase">Agree.</text>
              <text x="14" y="78" fill="#4d7c0f" font-size="7" text-anchor="end" class="uppercase">Neuro.</text>
            </svg>
          </div>
          <!-- Score bars with interpretations -->
          <div class="space-y-2 mt-2">
            <div v-for="trait in oceanTraits" :key="trait.key" class="space-y-0.5">
              <div class="flex justify-between text-xs">
                <span class="text-lime-600">{{ trait.label }}</span>
                <span class="text-white tabular-nums">{{ pct(trait.score) }}%</span>
              </div>
              <div class="h-px bg-lime-950">
                <div class="h-px bg-lime-500 transition-all duration-700" :style="{ width: pct(trait.score) + '%' }" />
              </div>
              <p class="text-[9px] text-lime-800 italic">{{ trait.interp }}</p>
            </div>
          </div>
        </section>

        <!-- Matching Ontology -->
        <section class="border border-lime-800 p-6 bg-black/30">
          <h2 class="text-lg mb-3 text-white uppercase tracking-widest">Matching Weights</h2>
          <div class="space-y-2 text-xs text-lime-600">
            <div class="flex justify-between">
              <span>Attachment compatibility</span>
              <span class="text-lime-400">40%</span>
            </div>
            <div class="flex justify-between">
              <span>Values congruence</span>
              <span class="text-lime-400">25%</span>
            </div>
            <div class="flex justify-between">
              <span>Big Five similarity</span>
              <span class="text-lime-400">20%</span>
            </div>
            <div class="flex justify-between">
              <span>Behavioral signals (Spotify/Strava/X)</span>
              <span class="text-lime-400">15%</span>
            </div>
          </div>
          <p class="mt-4 text-[10px] text-lime-800 italic leading-relaxed">
            Extraversion complementarity adds constructive friction. Neuroticism similarity stabilizes long-term satisfaction. Behavioral data fine-tunes raw psychological scores.
          </p>
        </section>
      </div>

      <!-- Right column -->
      <div class="space-y-8">

        <!-- Attachment Matrix -->
        <section class="border border-lime-800 p-6 bg-black/30">
          <h2 class="text-lg mb-2 text-white uppercase tracking-widest text-center">Attachment Matrix</h2>
          <p class="text-center text-[10px] text-lime-600 mb-4 uppercase tracking-widest">
            {{ attachmentStyleLabel }}
          </p>
          <div class="relative w-full aspect-square max-w-[260px] mx-auto border border-lime-900 bg-lime-950/10">
            <div class="absolute inset-y-0 left-1/2 w-px bg-lime-900"/>
            <div class="absolute inset-x-0 top-1/2 h-px bg-lime-900"/>
            <!-- Quadrant labels -->
            <span class="absolute top-2 left-2 text-[8px] text-lime-900 uppercase">Anxious-Preoccupied</span>
            <span class="absolute top-2 right-2 text-[8px] text-lime-900 uppercase text-right">Fearful-Avoidant</span>
            <span class="absolute bottom-2 left-2 text-[8px] text-lime-900 uppercase">Secure</span>
            <span class="absolute bottom-2 right-2 text-[8px] text-lime-900 uppercase text-right">Dismissive</span>
            <!-- Axis labels -->
            <span class="absolute top-1/2 left-1 -translate-y-1/2 text-[7px] text-lime-800 -rotate-90 origin-center whitespace-nowrap" style="transform: translateY(-50%) translateX(-28px) rotate(-90deg)">Anxiety →</span>
            <span class="absolute bottom-1 left-1/2 -translate-x-1/2 text-[7px] text-lime-800 whitespace-nowrap">Avoidance →</span>
            <!-- Plot point -->
            <div
              class="absolute w-3 h-3 bg-lime-400 rounded-full shadow-[0_0_10px_#a3e635] transition-all duration-1000"
              :style="{
                left: `${profile.ecr_r_scores.avoidance * 100}%`,
                top: `${(1 - profile.ecr_r_scores.anxiety) * 100}%`,
                transform: 'translate(-50%,-50%)'
              }"
            />
          </div>
          <!-- Numerical scores -->
          <div class="mt-4 grid grid-cols-2 gap-4 text-xs">
            <div>
              <span class="text-lime-600 uppercase tracking-wider block mb-0.5">Anxiety</span>
              <div class="h-px bg-lime-950 mt-1">
                <div class="h-px bg-blue-600 transition-all duration-700" :style="{ width: pct(profile.ecr_r_scores.anxiety) + '%' }"/>
              </div>
              <span class="text-white text-[10px]">{{ pct(profile.ecr_r_scores.anxiety) }}%</span>
            </div>
            <div>
              <span class="text-lime-600 uppercase tracking-wider block mb-0.5">Avoidance</span>
              <div class="h-px bg-lime-950 mt-1">
                <div class="h-px bg-purple-600 transition-all duration-700" :style="{ width: pct(profile.ecr_r_scores.avoidance) + '%' }"/>
              </div>
              <span class="text-white text-[10px]">{{ pct(profile.ecr_r_scores.avoidance) }}%</span>
            </div>
          </div>
        </section>

        <!-- Qualitative signals -->
        <section class="border border-lime-800 p-6 bg-black/30 grid grid-cols-2 gap-4 text-xs">
          <div>
            <span class="text-lime-600 uppercase tracking-wider block mb-1">Love Language</span>
            <span class="text-white font-semibold">{{ profile.love_language }}</span>
          </div>
          <div>
            <span class="text-lime-600 uppercase tracking-wider block mb-1">Values Cluster</span>
            <span class="text-white font-semibold">{{ profile.values_cluster }}</span>
          </div>
          <div class="col-span-2 pt-3 border-t border-lime-900/50">
            <span class="text-lime-600 uppercase tracking-wider block mb-1">Sociosexual Orientation</span>
            <span class="text-white font-semibold">{{ profile.sociosexual_orientation }}</span>
          </div>
        </section>

        <!-- Agent Synthesis -->
        <section class="border border-lime-800 p-6 bg-lime-900/5 relative overflow-hidden group">
          <div class="absolute inset-0 bg-lime-500/5 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"/>
          <div class="flex justify-between items-center mb-4 relative z-10">
            <h2 class="text-lg text-white uppercase tracking-widest">Agent Synthesis</h2>
            <button
              v-if="!profile.narrative && !generating"
              class="text-[10px] border border-lime-600 px-4 py-2 hover:bg-lime-900 text-lime-400 transition-all uppercase tracking-widest"
              @click="generateNarrative"
            >Initiate</button>
            <span v-else-if="generating" class="text-[10px] text-lime-500 animate-pulse uppercase tracking-widest">Synthesizing...</span>
          </div>

          <div v-if="profile.narrative" class="text-sm text-lime-300 leading-relaxed whitespace-pre-line relative z-10">
            {{ profile.narrative }}
          </div>
          <div v-else-if="generating" class="text-[10px] text-lime-800 font-mono italic space-y-1 relative z-10">
            <p>// Cross-referencing ECR-R vectors with OCEAN signatures</p>
            <p>// Injecting behavioral telemetry ({{ connectedProviders.join(', ') || 'none connected' }})</p>
            <p>// Awaiting Anthropic synthesis...</p>
          </div>
          <p v-else class="text-xs text-lime-800 italic relative z-10">
            No synthesis available. Click Initiate to construct a personalized narrative.
          </p>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useVibeStore } from '@/composables/useVibeStore'

// ── Constants ──────────────────────────────────────────────────────
const STEP_LABELS = ['Personality', 'Attachment', 'Identity']

// Big Five: 2 items per trait, scored 1–5. Reverse-scored items marked R.
const OCEAN_ITEMS = [
  { text: 'I have a rich imagination and love exploring abstract ideas.', trait: 'O' },
  { text: 'I am quick to understand new concepts and enjoy intellectual challenges.', trait: 'O' },
  { text: 'I am always prepared and like to plan things in advance.', trait: 'C' },
  { text: 'I pay attention to detail and follow through on commitments.', trait: 'C' },
  { text: 'I love being around people and am the life of the party.', trait: 'E' },
  { text: 'I feel energized after spending time in social settings.', trait: 'E' },
  { text: 'I feel empathy for others and make people feel at ease.', trait: 'A' },
  { text: 'I try to understand others\' perspectives before forming opinions.', trait: 'A' },
  { text: 'I am easily stressed and often feel anxious or unsettled.', trait: 'N' },
  { text: 'My mood fluctuates frequently and I can be easily upset.', trait: 'N' },
]

// ECR-R short form: 2 anxiety + 2 avoidance (item index → subscale)
// Avoidance item 3 is reverse-scored (high agreement = low avoidance)
const ATTACHMENT_ITEMS = [
  { text: 'I worry about being abandoned by the people I am close to.', subscale: 'anxiety' },
  { text: 'I need a lot of reassurance that I am loved.', subscale: 'anxiety' },
  { text: 'I prefer not to share my feelings or problems with partners.', subscale: 'avoidance' },
  { text: 'I feel comfortable depending on others for emotional support.', subscale: 'avoidance', reverse: true },
]

const LOVE_LANGUAGES = ['Words of Affirmation', 'Quality Time', 'Receiving Gifts', 'Acts of Service', 'Physical Touch']

const VALUES_CLUSTERS = [
  'Traditional / Family-oriented',
  'Career / Achievement-driven',
  'Creative / Artistic',
  'Progressive / Activist',
  'Adventure / Freedom-seeking',
  'Spiritual / Mindful',
]

const SOCIOSEXUAL_OPTIONS = [
  { value: 'Restricted',   label: 'Restricted',   sub: 'Seeking long-term' },
  { value: 'Moderate',     label: 'Moderate',      sub: 'Context-dependent' },
  { value: 'Unrestricted', label: 'Unrestricted',  sub: 'Open to short-term' },
]

// OCEAN interpretation thresholds
function oceanInterp(trait: string, score: number): string {
  const high = score >= 0.65
  const low  = score < 0.4
  const map: Record<string, [string, string, string]> = {
    O: ['Practical and concrete in thinking',       'Balanced pragmatism and curiosity',          'Highly imaginative, open to novel experiences'],
    C: ['Spontaneous, flexible, adaptive',           'Blends structure and adaptability',          'Organized, disciplined, follows through'],
    E: ['Introspective, gains energy from solitude', 'Comfortable in both social and solo contexts', 'Energized by people, thrives in company'],
    A: ['Direct and competitive, prioritizes logic', 'Cooperative but holds firm on key values',    'Empathic, harmonious, trusts others readily'],
    N: ['Emotionally stable, rarely rattled',        'Moderate emotional reactivity',              'Emotionally sensitive, internalizes stress'],
  }
  const [lo, mid, hi] = map[trait] ?? ['', '', '']
  return low ? lo : high ? hi : mid
}

// ── State ──────────────────────────────────────────────────────────
const step = ref(0)
const oceanAnswers  = ref<(number | undefined)[]>(Array(OCEAN_ITEMS.length).fill(undefined))
const attachAnswers = ref<(number | undefined)[]>(Array(ATTACHMENT_ITEMS.length).fill(undefined))

const form = ref({
  love_language:  LOVE_LANGUAGES[1],
  values_cluster: VALUES_CLUSTERS[0],
  sociosexual:    'Moderate',
})

const profile    = ref<any>(null)
const loading    = ref(true)
const submitting = ref(false)
const generating = ref(false)

const { oauthState } = useVibeStore()

// ── Derived ────────────────────────────────────────────────────────
const oceanComplete     = computed(() => oceanAnswers.value.every(v => v !== undefined))
const attachmentComplete = computed(() => attachAnswers.value.every(v => v !== undefined))
const identityComplete  = computed(() => !!form.value.love_language && !!form.value.values_cluster && !!form.value.sociosexual)

const connectedProviders = computed(() => {
  if (!oauthState.value) return []
  return (Object.keys(oauthState.value) as (keyof typeof oauthState.value)[])
    .filter(k => oauthState.value[k].connected)
})

// Compute normalized OCEAN scores from Likert items
const computedScores = computed(() => {
  const scores: Record<string, number[]> = { O: [], C: [], E: [], A: [], N: [] }
  OCEAN_ITEMS.forEach((item, i) => {
    const v = oceanAnswers.value[i]
    if (v !== undefined) scores[item.trait].push((v - 1) / 4)
  })
  const avg = (arr: number[]) => arr.length ? arr.reduce((s, n) => s + n, 0) / arr.length : 0.5
  return { O: avg(scores.O), C: avg(scores.C), E: avg(scores.E), A: avg(scores.A), N: avg(scores.N) }
})

// Radar polygon — pentagon, radius 80, center 100,100
const radarPoints = computed(() => {
  const s = profile.value?.ipip_neo_scores ?? computedScores.value
  const pts = [
    [s.O, 270], [s.C, 342], [s.E, 54], [s.A, 126], [s.N, 198],
  ].map(([score, deg]) => {
    const r = (score as number) * 80
    const rad = ((deg as number) * Math.PI) / 180
    return `${100 + r * Math.cos(rad)},${100 + r * Math.sin(rad)}`
  })
  return pts.join(' ')
})

const oceanTraits = computed(() => {
  const s = profile.value?.ipip_neo_scores ?? {}
  return [
    { key: 'O', label: 'Openness',          score: s.O ?? 0, interp: oceanInterp('O', s.O ?? 0) },
    { key: 'C', label: 'Conscientiousness', score: s.C ?? 0, interp: oceanInterp('C', s.C ?? 0) },
    { key: 'E', label: 'Extraversion',      score: s.E ?? 0, interp: oceanInterp('E', s.E ?? 0) },
    { key: 'A', label: 'Agreeableness',     score: s.A ?? 0, interp: oceanInterp('A', s.A ?? 0) },
    { key: 'N', label: 'Neuroticism',       score: s.N ?? 0, interp: oceanInterp('N', s.N ?? 0) },
  ]
})

const attachmentStyleLabel = computed(() => {
  const ecr = profile.value?.ecr_r_scores
  if (!ecr) return ''
  const { anxiety, avoidance } = ecr
  if (anxiety < 0.5 && avoidance < 0.5) return 'Secure — comfortable with closeness and interdependence'
  if (anxiety >= 0.5 && avoidance < 0.5) return 'Anxious-Preoccupied — craves closeness, fears abandonment'
  if (anxiety < 0.5 && avoidance >= 0.5) return 'Dismissive-Avoidant — values independence, suppresses need'
  return 'Fearful-Avoidant — desires closeness but fears vulnerability'
})

// ── Helpers ────────────────────────────────────────────────────────
function pct(v: number) { return Math.round(v * 100) }

const getHeaders = () => {
  const token = localStorage.getItem('channelzero-jwt')
  return { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }
}

// ── Lifecycle ──────────────────────────────────────────────────────
onMounted(async () => {
  try {
    const res = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/psychometrics/profile`, {
      headers: getHeaders(),
    })
    if (res.ok) profile.value = await res.json()
  } catch { /* no profile yet */ } finally {
    loading.value = false
  }
})

// ── Actions ────────────────────────────────────────────────────────
const submitAssessment = async () => {
  submitting.value = true
  // Compute attachment scores from Likert responses
  const anxietyItems  = ATTACHMENT_ITEMS.map((item, i) => ({ ...item, answer: attachAnswers.value[i]! }))
    .filter(item => item.subscale === 'anxiety')
  const avoidanceItems = ATTACHMENT_ITEMS.map((item, i) => ({ ...item, answer: attachAnswers.value[i]! }))
    .filter(item => item.subscale === 'avoidance')

  const anxScore = anxietyItems.reduce((s, item) => s + (item.answer - 1) / 6, 0) / anxietyItems.length
  const avoScore = avoidanceItems.reduce((s, item) => {
    const v = (item as any).reverse ? (8 - item.answer - 1) / 6 : (item.answer - 1) / 6
    return s + v
  }, 0) / avoidanceItems.length

  const s = computedScores.value
  try {
    const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'
    const res = await fetch(`${API}/api/psychometrics/submit`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({
        responses: {
          O_score: s.O, C_score: s.C, E_score: s.E, A_score: s.A, N_score: s.N,
          anxiety_score: anxScore,
          avoidance_score: avoScore,
          love_language: form.value.love_language,
          values_cluster: form.value.values_cluster,
          sociosexual: form.value.sociosexual,
        },
      }),
    })
    if (res.ok) {
      const data = await res.json()
      profile.value = data.profile
    }
  } catch { /* noop */ } finally {
    submitting.value = false
  }
}

const generateNarrative = async () => {
  generating.value = true
  try {
    const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'
    const res = await fetch(`${API}/api/psychometrics/narrative`, {
      method: 'POST',
      headers: getHeaders(),
    })
    if (res.ok) {
      const data = await res.json()
      profile.value.narrative = data.narrative
    } else {
      const err = await res.json().catch(() => ({}))
      alert(err.detail || 'Error generating narrative. Do you have an API key set?')
    }
  } catch { /* noop */ } finally {
    generating.value = false
  }
}
</script>

<style scoped>
/* Hide number spinner */
input[type="number"]::-webkit-inner-spin-button,
input[type="number"]::-webkit-outer-spin-button { -webkit-appearance: none; margin: 0; }
input[type="number"] { -moz-appearance: textfield; }
</style>
