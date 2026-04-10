<template>
  <div class="x-scene">

    <!-- Tab switcher -->
    <div class="tab-bar">
      <button
        class="tab-btn"
        :class="{ active: tab === 'signal' }"
        @click="tab = 'signal'"
      >signal</button>
      <span class="tab-sep">·</span>
      <button
        class="tab-btn"
        :class="{ active: tab === 'imprint' }"
        @click="tab = 'imprint'"
      >imprint</button>
    </div>

    <!-- Back nav -->
    <router-link to="/calibrate" class="back-link">← calibrate</router-link>

    <!-- Loading -->
    <div v-if="!loaded" class="center-state">
      <p class="mono-sm">parsing neurotic footprint...</p>
    </div>

    <!-- No data -->
    <div v-else-if="!profile" class="center-state">
      <p class="mono-sm">no x data yet —</p>
      <router-link to="/calibrate" class="link-dim">connect on calibrate</router-link>
    </div>

    <!-- ── SIGNAL VIEW ─────────────────────────────────────────── -->
    <div v-else-if="tab === 'signal'" class="panel signal-panel">

      <!-- Profile header -->
      <div class="card profile-card">
        <div class="profile-top">
          <div class="x-avatar">
            <span class="x-icon">𝕏</span>
          </div>
          <div class="profile-meta">
            <p class="username">@{{ profile.username }}</p>
            <p class="bio">{{ profile.bio || 'no bio' }}</p>
          </div>
        </div>
        <p class="account-age">{{ accountAge }}</p>
      </div>

      <!-- Reach metrics 2×2 -->
      <div class="metric-grid">
        <div class="metric-card">
          <p class="metric-val">{{ fmt(profile.followers) }}</p>
          <p class="metric-label">followers</p>
        </div>
        <div class="metric-card">
          <p class="metric-val">{{ fmt(profile.following_count) }}</p>
          <p class="metric-label">following</p>
        </div>
        <div class="metric-card">
          <p class="metric-val">{{ fmt(profile.tweet_count) }}</p>
          <p class="metric-label">tweets</p>
        </div>
        <div class="metric-card">
          <p class="metric-val">{{ fmt(profile.listed_count) }}</p>
          <p class="metric-label">lists</p>
        </div>
      </div>

      <!-- Behavioral signal bars -->
      <div class="card bars-card">
        <p class="card-label">behavioral signal</p>
        <div v-for="bar in signalBars" :key="bar.key" class="bar-row">
          <span class="bar-name">{{ bar.label }}</span>
          <div class="bar-track">
            <div
              class="bar-fill"
              :style="{ width: `${bar.pct}%`, background: bar.color }"
            ></div>
          </div>
          <span class="bar-val">{{ bar.display }}</span>
        </div>
      </div>

      <!-- FF ratio card -->
      <div class="card ratio-card">
        <p class="card-label">follower / following ratio</p>
        <p class="ratio-val">{{ ffRatio }}</p>
        <p class="ratio-desc">{{ ffLabel }}</p>
      </div>

      <!-- Engagement -->
      <div class="card engage-card">
        <p class="card-label">avg engagement per tweet</p>
        <div class="engage-row">
          <div class="engage-item">
            <p class="engage-num">{{ profile.engagement_avg?.likes?.toFixed(1) ?? '—' }}</p>
            <p class="engage-sub">likes</p>
          </div>
          <div class="engage-divider"></div>
          <div class="engage-item">
            <p class="engage-num">{{ profile.engagement_avg?.retweets?.toFixed(1) ?? '—' }}</p>
            <p class="engage-sub">retweets</p>
          </div>
          <div class="engage-divider"></div>
          <div class="engage-item">
            <p class="engage-num">{{ profile.recent_likes_given }}</p>
            <p class="engage-sub">likes given</p>
          </div>
        </div>
      </div>

      <!-- Posting hours chart -->
      <div v-if="hasHours" class="card hours-card">
        <p class="card-label">posting activity (UTC hour)</p>
        <div class="hours-grid">
          <div
            v-for="h in 24"
            :key="h"
            class="hour-bar"
            :style="{ height: `${hourHeight(h - 1)}px`, background: hourColor(h - 1) }"
            :title="`${h - 1}:00 — ${postingHours[String(h - 1)] ?? 0} tweets`"
          ></div>
        </div>
        <div class="hours-labels">
          <span>0h</span><span>6h</span><span>12h</span><span>18h</span><span>23h</span>
        </div>
      </div>

      <!-- Tweet samples -->
      <div v-if="profile.tweet_samples?.length" class="card samples-card">
        <p class="card-label">recent signal</p>
        <div v-for="(s, i) in profile.tweet_samples" :key="i" class="sample">
          <p class="sample-text">"{{ s }}"</p>
        </div>
      </div>

    </div>

    <!-- ── IMPRINT VIEW ────────────────────────────────────────── -->
    <div v-else class="panel imprint-panel">

      <div v-if="!analysisDone && !analysisLoading" class="imprint-prompt">
        <p class="mono-sm">your neurotic imprint, analyzed.</p>
        <button class="analyze-btn" @click="runAnalysis">generate imprint</button>
      </div>

      <div v-if="analysisLoading" class="center-state">
        <p class="mono-sm">reading your signal...</p>
        <div class="pulse-ring"></div>
      </div>

      <div v-if="analysisDone && narrative" class="narrative-wrap">
        <p class="card-label" style="margin-bottom:1.5rem">neurotic imprint</p>
        <div class="narrative-body">
          <p
            v-for="(para, i) in narrativeParagraphs"
            :key="i"
            class="narrative-para"
          >{{ para }}</p>
        </div>
        <button class="rerun-btn" @click="runAnalysis">↺ regenerate</button>
      </div>

      <div v-if="analysisError" class="center-state">
        <p class="mono-sm error-text">{{ analysisError }}</p>
      </div>

    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/composables/useAuthStore'

const { apiFetch } = useAuthStore()

interface TwitterProfile {
  username: string
  bio: string
  followers: number
  following_count: number
  tweet_count: number
  listed_count: number
  account_created: string
  recent_tweet_count: number
  avg_tweet_length: number
  recent_likes_given: number
  high_profile_follows: number
  engagement_avg?: { likes: number; retweets: number }
  posting_hours?: Record<string, number>
  tweet_samples?: string[]
  language?: string
}

const tab             = ref<'signal' | 'imprint'>('signal')
const profile         = ref<TwitterProfile | null>(null)
const loaded          = ref(false)
const narrative       = ref('')
const analysisDone    = ref(false)
const analysisLoading = ref(false)
const analysisError   = ref('')

onMounted(async () => {
  try {
    profile.value = await apiFetch<TwitterProfile | null>('/api/twitter/profile')
  } catch { /* no data */ }
  loaded.value = true
})

async function runAnalysis() {
  analysisLoading.value = true
  analysisDone.value = false
  analysisError.value = ''
  try {
    const res = await apiFetch<{ narrative: string }>('/api/twitter/analyze')
    narrative.value = res.narrative
    analysisDone.value = true
  } catch (e: any) {
    analysisError.value = e?.detail ?? 'analysis failed — try again'
  } finally {
    analysisLoading.value = false
  }
}

// ── Computed ──────────────────────────────────────────────────────────────────

const accountAge = computed(() => {
  if (!profile.value?.account_created) return ''
  const created = new Date(profile.value.account_created)
  const years = Math.floor((Date.now() - created.getTime()) / (1000 * 60 * 60 * 24 * 365))
  const mo = created.toLocaleString('default', { month: 'long', year: 'numeric' })
  return `joined ${mo} · ${years}y old account`
})

const ffRatio = computed(() => {
  const p = profile.value
  if (!p) return '—'
  if (!p.following_count) return '∞'
  return (p.followers / p.following_count).toFixed(2)
})

const ffLabel = computed(() => {
  const r = parseFloat(ffRatio.value)
  if (isNaN(r)) return ''
  if (r >= 10) return 'broadcaster — heavily asymmetric reach'
  if (r >= 2)  return 'established — more watchers than peers'
  if (r >= 0.8) return 'peer network — balanced exchange'
  return 'consumer — following more than followed'
})

const signalBars = computed(() => {
  const p = profile.value
  if (!p) return []
  return [
    {
      key: 'tweet_len',
      label: 'verbosity',
      pct: Math.min(100, (p.avg_tweet_length / 280) * 100),
      display: `${p.avg_tweet_length} chars`,
      color: '#818cf8',
    },
    {
      key: 'high_profile',
      label: 'elite orbit',
      pct: Math.min(100, (p.high_profile_follows / Math.max(1, p.following_count)) * 100 * 5),
      display: `${p.high_profile_follows} accounts`,
      color: '#f59e0b',
    },
    {
      key: 'listed',
      label: 'influence',
      pct: Math.min(100, Math.log10(Math.max(1, p.listed_count)) / 4 * 100),
      display: fmt(p.listed_count),
      color: '#34d399',
    },
    {
      key: 'passive',
      label: 'passive ratio',
      pct: Math.min(100, (p.recent_likes_given / Math.max(1, p.recent_tweet_count + p.recent_likes_given)) * 100),
      display: p.recent_likes_given > p.recent_tweet_count ? 'mostly consumes' : 'mostly posts',
      color: '#f87171',
    },
  ]
})

const postingHours = computed(() => profile.value?.posting_hours ?? {})
const hasHours = computed(() => Object.keys(postingHours.value).length > 0)
const maxHourCount = computed(() => Math.max(1, ...Object.values(postingHours.value)))

function hourHeight(h: number): number {
  const count = postingHours.value[String(h)] ?? 0
  return Math.round((count / maxHourCount.value) * 40)
}
function hourColor(h: number): string {
  const count = postingHours.value[String(h)] ?? 0
  if (!count) return 'rgba(255,255,255,0.05)'
  const intensity = count / maxHourCount.value
  return `rgba(129, 140, 248, ${0.2 + intensity * 0.8})`
}

const narrativeParagraphs = computed(() =>
  narrative.value.split(/\n\n+/).filter(Boolean)
)

function fmt(n: number): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M'
  if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K'
  return String(n)
}
</script>

<style scoped>
.x-scene {
  position: fixed;
  inset: 0;
  background: #08060e;
  overflow-y: auto;
  font-family: monospace;
  color: #94a3b8;
}

/* ── Navigation ── */
.tab-bar {
  position: fixed;
  top: 1.5rem;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: rgba(8, 6, 14, 0.85);
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 100px;
  padding: 0.4rem 1rem;
  backdrop-filter: blur(12px);
  z-index: 50;
}
.tab-btn {
  background: none;
  border: none;
  color: #475569;
  font-family: monospace;
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  cursor: pointer;
  transition: color 0.15s;
  padding: 0;
}
.tab-btn.active { color: #e2e8f0; }
.tab-btn:hover { color: #94a3b8; }
.tab-sep { color: #1e293b; font-size: 0.7rem; }

.back-link {
  position: fixed;
  top: 1.5rem;
  left: 1.5rem;
  font-size: 0.65rem;
  color: #334155;
  text-decoration: none;
  z-index: 50;
  transition: color 0.15s;
}
.back-link:hover { color: #64748b; }

/* ── States ── */
.center-state {
  position: fixed;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
}
.mono-sm {
  font-size: 0.75rem;
  color: #475569;
  font-family: monospace;
}
.link-dim {
  font-size: 0.7rem;
  color: #6366f1;
  text-decoration: none;
}

/* ── Panels ── */
.panel {
  max-width: 560px;
  margin: 5rem auto 4rem;
  padding: 0 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.875rem;
}

/* ── Cards ── */
.card {
  background: rgba(255,255,255,0.025);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 1rem;
  padding: 1.1rem 1.25rem;
}
.card-label {
  font-size: 0.55rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: #334155;
  font-weight: 600;
  margin-bottom: 0.75rem;
}

/* ── Profile card ── */
.profile-card { }
.profile-top {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 0.75rem;
}
.x-avatar {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.x-icon { font-size: 1.1rem; color: #e2e8f0; }
.profile-meta { flex: 1; }
.username {
  font-size: 0.9rem;
  color: #e2e8f0;
  margin-bottom: 0.25rem;
}
.bio {
  font-size: 0.68rem;
  color: #64748b;
  line-height: 1.5;
  font-style: italic;
}
.account-age {
  font-size: 0.6rem;
  color: #334155;
}

/* ── Metric grid ── */
.metric-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.875rem;
}
.metric-card {
  background: rgba(255,255,255,0.025);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 0.875rem;
  padding: 0.9rem 1rem;
  text-align: center;
}
.metric-val {
  font-size: 1.5rem;
  color: #e2e8f0;
  font-weight: 600;
  margin-bottom: 0.2rem;
  letter-spacing: -0.02em;
}
.metric-label {
  font-size: 0.55rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #334155;
}

/* ── Bar rows ── */
.bar-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.45rem;
}
.bar-name {
  font-size: 0.6rem;
  color: #64748b;
  width: 72px;
  flex-shrink: 0;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.bar-track {
  flex: 1;
  height: 3px;
  background: rgba(255,255,255,0.06);
  border-radius: 2px;
  overflow: hidden;
}
.bar-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 1s cubic-bezier(0.4, 0, 0.2, 1);
  opacity: 0.85;
}
.bar-val {
  font-size: 0.6rem;
  color: #475569;
  width: 80px;
  text-align: right;
  flex-shrink: 0;
}

/* ── Ratio card ── */
.ratio-val {
  font-size: 2.5rem;
  color: #e2e8f0;
  font-weight: 600;
  letter-spacing: -0.03em;
  margin-bottom: 0.3rem;
}
.ratio-desc {
  font-size: 0.65rem;
  color: #475569;
  font-style: italic;
}

/* ── Engagement ── */
.engage-row {
  display: flex;
  align-items: center;
  gap: 0;
}
.engage-item {
  flex: 1;
  text-align: center;
}
.engage-num {
  font-size: 1.4rem;
  color: #e2e8f0;
  font-weight: 600;
  letter-spacing: -0.02em;
  margin-bottom: 0.2rem;
}
.engage-sub {
  font-size: 0.55rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #334155;
}
.engage-divider {
  width: 1px;
  height: 36px;
  background: rgba(255,255,255,0.06);
}

/* ── Hours chart ── */
.hours-grid {
  display: flex;
  align-items: flex-end;
  gap: 3px;
  height: 48px;
  margin-bottom: 0.35rem;
}
.hour-bar {
  flex: 1;
  min-height: 2px;
  border-radius: 2px 2px 0 0;
  transition: height 0.6s ease;
  cursor: default;
}
.hours-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.5rem;
  color: #334155;
}

/* ── Tweet samples ── */
.sample {
  border-left: 2px solid rgba(255,255,255,0.08);
  padding-left: 0.75rem;
  margin-bottom: 0.6rem;
}
.sample:last-child { margin-bottom: 0; }
.sample-text {
  font-size: 0.68rem;
  color: #64748b;
  line-height: 1.55;
  font-style: italic;
}

/* ── Imprint panel ── */
.imprint-panel {
  align-items: center;
  min-height: calc(100vh - 9rem);
  justify-content: center;
}
.imprint-prompt {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
  margin-top: 4rem;
}
.analyze-btn {
  background: rgba(99, 102, 241, 0.12);
  border: 1px solid rgba(99, 102, 241, 0.3);
  color: #818cf8;
  font-family: monospace;
  font-size: 0.72rem;
  padding: 0.6rem 1.5rem;
  border-radius: 100px;
  cursor: pointer;
  transition: all 0.2s;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}
.analyze-btn:hover {
  background: rgba(99, 102, 241, 0.2);
  border-color: rgba(99, 102, 241, 0.5);
}

/* ── Pulse ring ── */
.pulse-ring {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 1px solid rgba(99, 102, 241, 0.4);
  animation: pulse-expand 1.5s ease-out infinite;
}
@keyframes pulse-expand {
  0%   { transform: scale(0.8); opacity: 0.8; }
  100% { transform: scale(1.8); opacity: 0; }
}

/* ── Narrative ── */
.narrative-wrap {
  width: 100%;
  padding: 0.5rem 0;
}
.narrative-body {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  margin-bottom: 2rem;
}
.narrative-para {
  font-size: 0.78rem;
  line-height: 1.8;
  color: #94a3b8;
}
.rerun-btn {
  background: none;
  border: none;
  color: #334155;
  font-family: monospace;
  font-size: 0.6rem;
  cursor: pointer;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  transition: color 0.15s;
  padding: 0;
}
.rerun-btn:hover { color: #64748b; }

.error-text { color: #f87171; }
</style>
