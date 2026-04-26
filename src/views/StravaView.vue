<template>
  <div class="min-h-screen bg-gray-900 text-white relative overflow-hidden">

    <!-- Background pulse layer -->
    <div class="absolute inset-0 pointer-events-none">
      <div class="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] rounded-full bg-orange-400/5 blur-3xl animate-breathe" />
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center min-h-screen">
      <div class="text-center space-y-4 animate-fade-in">
        <div class="w-10 h-10 border-2 border-orange-400 border-t-transparent rounded-full animate-spin mx-auto" />
        <p class="text-sm text-gray-400 tracking-widest uppercase">reading somatic ledger...</p>
      </div>
    </div>

    <!-- Error / not connected -->
    <div v-else-if="error" class="flex items-center justify-center min-h-screen">
      <div class="text-center space-y-4 animate-fade-in">
        <p class="text-sm text-gray-400 tracking-widest uppercase">no strava data yet</p>
        <router-link to="/calibrate" class="inline-block px-6 py-2 border border-orange-400/40 text-orange-400 text-sm tracking-wider uppercase hover:bg-orange-400/10 transition-colors rounded">
          connect strava
        </router-link>
      </div>
    </div>

    <!-- Main content -->
    <div v-else-if="data" class="relative z-10 max-w-4xl mx-auto px-4 py-12 sm:py-20 space-y-12 animate-fade-in">

      <!-- Header -->
      <header class="text-center space-y-2">
        <h1 class="text-3xl sm:text-4xl font-light tracking-widest uppercase text-orange-400">The Somatic Ledger</h1>
        <p v-if="data.athlete_name" class="text-sm text-gray-400 tracking-wider">{{ data.athlete_name }}</p>
      </header>

      <!-- Activity Ring -->
      <section class="flex flex-col items-center space-y-6">
        <div class="relative w-56 h-56 sm:w-64 sm:h-64">
          <!-- Conic ring -->
          <div
            class="w-full h-full rounded-full"
            :style="{ background: ringGradient }"
          />
          <!-- Inner cutout -->
          <div class="absolute inset-6 sm:inset-8 rounded-full bg-gray-900 flex items-center justify-center">
            <div class="text-center">
              <p class="text-2xl sm:text-3xl font-light text-white">{{ data.recent_count }}</p>
              <p class="text-xs text-gray-500 tracking-wider uppercase">activities</p>
            </div>
          </div>
        </div>
        <!-- Legend -->
        <div class="flex flex-wrap justify-center gap-4">
          <div v-for="seg in ringSegments" :key="seg.type" class="flex items-center gap-2">
            <span class="w-3 h-3 rounded-full" :style="{ background: seg.color }" />
            <span class="text-xs text-gray-300">{{ seg.type }} <span class="text-gray-500">({{ seg.count }})</span></span>
          </div>
        </div>
      </section>

      <!-- Stats Grid -->
      <section class="grid grid-cols-2 sm:grid-cols-3 gap-4">
        <div v-for="stat in statsGrid" :key="stat.label" class="bg-gray-800/50 border border-gray-700/50 rounded-lg p-4 text-center space-y-1">
          <p class="text-xs text-gray-500 tracking-wider uppercase">{{ stat.label }}</p>
          <p :class="['text-xl sm:text-2xl font-light', stat.pulse ? 'animate-pulse-hr text-red-400' : 'text-white']">
            {{ stat.value }}
          </p>
          <p v-if="stat.unit" class="text-xs text-gray-600">{{ stat.unit }}</p>
        </div>
      </section>

      <!-- All-Time Records -->
      <section class="space-y-4">
        <h2 class="text-xs text-gray-500 tracking-widest uppercase text-center">All-Time Ledger</h2>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div v-if="data.all_time_runs" class="bg-gray-800/30 border border-orange-400/20 rounded-lg p-5 flex items-center gap-4">
            <div class="text-3xl">🏃</div>
            <div>
              <p class="text-lg font-light text-orange-400">{{ fmt(data.all_time_runs) }} runs</p>
              <p class="text-sm text-gray-400">{{ fmt(data.all_time_run_distance_km) }} km total</p>
            </div>
          </div>
          <div v-if="data.all_time_rides" class="bg-gray-800/30 border border-blue-400/20 rounded-lg p-5 flex items-center gap-4">
            <div class="text-3xl">🚴</div>
            <div>
              <p class="text-lg font-light text-blue-400">{{ fmt(data.all_time_rides) }} rides</p>
              <p class="text-sm text-gray-400">{{ fmt(data.all_time_ride_distance_km) }} km total</p>
            </div>
          </div>
        </div>
      </section>

      <!-- Exertion Profile -->
      <section v-if="data.avg_heartrate && data.max_heartrate" class="space-y-3">
        <h2 class="text-xs text-gray-500 tracking-widest uppercase text-center">Exertion Profile</h2>
        <div class="bg-gray-800/30 border border-gray-700/50 rounded-lg p-5 space-y-3">
          <div class="flex justify-between text-xs text-gray-500">
            <span>Rest</span>
            <span>{{ Math.round(exertionPct * 100) }}% of ceiling</span>
            <span>Max</span>
          </div>
          <div class="h-4 rounded-full overflow-hidden bg-gray-700/50 relative">
            <div
              class="h-full rounded-full transition-all duration-1000 ease-out"
              :style="{ width: `${exertionPct * 100}%`, background: exertionGradient }"
            />
            <!-- Max marker -->
            <div class="absolute right-0 top-0 h-full w-0.5 bg-red-500/60" />
          </div>
          <div class="flex justify-between text-sm">
            <span class="text-gray-400">avg <span class="text-orange-400 font-medium">{{ Math.round(data.avg_heartrate) }}</span> bpm</span>
            <span class="text-gray-400">max <span class="text-red-400 font-medium">{{ Math.round(data.max_heartrate) }}</span> bpm</span>
          </div>
        </div>
      </section>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/composables/useAuthStore'

interface StravaProfile {
  athlete_name: string
  activity_types: Record<string, number>
  recent_count: number
  total_elevation_m: number
  total_distance_km: number
  total_moving_hours: number
  avg_heartrate: number | null
  max_heartrate: number | null
  all_time_runs: number
  all_time_run_distance_km: number
  all_time_rides: number
  all_time_ride_distance_km: number
}

const { apiFetch } = useAuthStore()

const data = ref<StravaProfile | null>(null)
const loading = ref(true)
const error = ref(false)

// ── Activity type colors ────────────────────────────────────────────
const typeColors: Record<string, string> = {
  Run: '#fb923c',       // orange-400
  Ride: '#60a5fa',      // blue-400
  Swim: '#2dd4bf',      // teal-400
  Hike: '#a78bfa',      // violet-400
  Walk: '#fbbf24',      // amber-400
  Yoga: '#f472b6',      // pink-400
  Workout: '#34d399',   // emerald-400
  WeightTraining: '#c084fc', // purple-400
}
const fallbackColors = ['#94a3b8', '#64748b', '#78716c', '#a3a3a3']

function colorFor(type: string, idx: number): string {
  return typeColors[type] || fallbackColors[idx % fallbackColors.length]
}

// ── Ring segments ───────────────────────────────────────────────────
const ringSegments = computed(() => {
  if (!data.value) return []
  const types = data.value.activity_types
  const entries = Object.entries(types).sort((a, b) => b[1] - a[1])
  return entries.map(([type, count], i) => ({
    type,
    count,
    color: colorFor(type, i),
  }))
})

const ringGradient = computed(() => {
  const segs = ringSegments.value
  if (!segs.length) return 'conic-gradient(#374151 0deg 360deg)'
  const total = segs.reduce((s, seg) => s + seg.count, 0)
  if (!total) return 'conic-gradient(#374151 0deg 360deg)'

  const parts: string[] = []
  let angle = 0
  for (const seg of segs) {
    const sweep = (seg.count / total) * 360
    parts.push(`${seg.color} ${angle}deg ${angle + sweep}deg`)
    angle += sweep
  }
  return `conic-gradient(${parts.join(', ')})`
})

// ── Stats grid ──────────────────────────────────────────────────────
function fmt(n: number | undefined | null): string {
  if (n == null) return '—'
  return Math.round(n).toLocaleString()
}

function fmtHours(h: number | undefined | null): string {
  if (h == null) return '—'
  const hours = Math.floor(h)
  const mins = Math.round((h - hours) * 60)
  return `${hours}h ${mins}m`
}

const statsGrid = computed(() => {
  if (!data.value) return []
  const d = data.value
  return [
    { label: 'Total Distance', value: fmt(d.total_distance_km), unit: 'km' },
    { label: 'Total Elevation', value: fmt(d.total_elevation_m), unit: 'm' },
    { label: 'Moving Time', value: fmtHours(d.total_moving_hours), unit: null },
    { label: 'Avg Heart Rate', value: d.avg_heartrate ? `${Math.round(d.avg_heartrate)}` : '—', unit: 'bpm', pulse: !!d.avg_heartrate },
    { label: 'Recent Activities', value: d.recent_count.toString(), unit: 'last 30 days' },
    { label: 'Max Heart Rate', value: d.max_heartrate ? `${Math.round(d.max_heartrate)}` : '—', unit: 'bpm' },
  ]
})

// ── Exertion profile ────────────────────────────────────────────────
const exertionPct = computed(() => {
  if (!data.value?.avg_heartrate || !data.value?.max_heartrate) return 0
  return data.value.avg_heartrate / data.value.max_heartrate
})

const exertionGradient = computed(() => {
  return 'linear-gradient(90deg, #fb923c, #ef4444)'
})

// ── Fetch ───────────────────────────────────────────────────────────
onMounted(async () => {
  try {
    data.value = await apiFetch<StravaProfile>('/api/strava/profile')
  } catch {
    error.value = true
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
@keyframes fade-in {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}
.animate-fade-in {
  animation: fade-in 0.6s ease-out both;
}

@keyframes breathe {
  0%, 100% { opacity: 0.04; transform: translate(-50%, 0) scale(1); }
  50% { opacity: 0.08; transform: translate(-50%, 0) scale(1.05); }
}
.animate-breathe {
  animation: breathe 6s ease-in-out infinite;
}

@keyframes pulse-hr {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
.animate-pulse-hr {
  animation: pulse-hr 1s ease-in-out infinite;
}
</style>
