<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '@/composables/useAuthStore'

const props = defineProps<{
  coherence: number
  syncCount: number
  sessionDuration: number
  dominantPhase: string
}>()

const emit = defineEmits<{ close: [] }>()

const { apiFetch } = useAuthStore()

const visible = ref(false)
const submitting = ref(false)
const submitted = ref(false)
const selectedValue = ref<number | null>(null)

interface NextItem {
  item_id: string
  instrument: string
  text: string
  scale: string
  options: string[] | null
  connector_affinity: string
  progress: { answered: number; core_total: number }
}

const nextItem = ref<NextItem | null>(null)
const connectorData = ref<Record<string, unknown> | null>(null)
const pickedConnector = ref<string>('spotify')

// ── Connector round-robin ────────────────────────────────────────
const CONNECTOR_KEY = 'cz-last-reflect-connector'
const CONNECTORS = ['spotify', 'strava']

function pickConnector(): string {
  const last = localStorage.getItem(CONNECTOR_KEY)
  const idx = last ? (CONNECTORS.indexOf(last) + 1) % CONNECTORS.length : 0
  const pick = CONNECTORS[idx]
  localStorage.setItem(CONNECTOR_KEY, pick)
  return pick
}

// ── Trance summary line ─────────────────────────────────────────
const tranceLine = computed(() => {
  const mins = Math.floor(props.sessionDuration / 60000)
  const secs = Math.floor((props.sessionDuration % 60000) / 1000)
  const time = mins > 0 ? `${mins}m ${secs}s` : `${secs}s`
  return `coherence ${Math.round(props.coherence)} · ${time} · ${props.dominantPhase}`
})

// ── Spotify data cards ──────────────────────────────────────────
const spotifyStats = computed(() => {
  if (!connectorData.value || pickedConnector.value !== 'spotify') return []
  const d = connectorData.value as any
  const stats: { label: string; value: string }[] = []

  if (d.genres?.length >= 2) {
    stats.push({ label: 'genres', value: `${d.genres[0]} · ${d.genres[1]}` })
  } else if (d.genres?.length === 1) {
    stats.push({ label: 'genre', value: d.genres[0] })
  }

  if (d.audio_avg?.valence != null) {
    const v = d.audio_avg.valence
    const mood = v < 0.3 ? 'melancholic' : v < 0.6 ? 'bittersweet' : 'luminous'
    stats.push({ label: 'valence', value: `${(v * 100).toFixed(0)}% — ${mood}` })
  }

  if (d.top_artists?.length) {
    stats.push({ label: 'top artist', value: d.top_artists[0] })
  }

  return stats.slice(0, 3)
})

// ── Strava data cards ───────────────────────────────────────────
const stravaStats = computed(() => {
  if (!connectorData.value || pickedConnector.value !== 'strava') return []
  const d = connectorData.value as any
  const stats: { label: string; value: string }[] = []

  if (d.activity_types) {
    const entries = Object.entries(d.activity_types) as [string, number][]
    if (entries.length) {
      const [type, count] = entries.sort((a, b) => (b[1] as number) - (a[1] as number))[0]
      stats.push({ label: 'dominant', value: `${count} ${type.toLowerCase()}s` })
    }
  }

  if (d.total_distance_km) {
    stats.push({ label: 'distance', value: `${Math.round(d.total_distance_km)} km` })
  }

  if (d.avg_heartrate) {
    stats.push({
      label: 'heartrate',
      value: `HR ${Math.round(d.avg_heartrate)} bpm · coherence ${Math.round(props.coherence)}`,
    })
  }

  return stats.slice(0, 3)
})

const connectorStats = computed(() =>
  pickedConnector.value === 'spotify' ? spotifyStats.value : stravaStats.value
)

const connectorLabel = computed(() =>
  pickedConnector.value === 'spotify' ? '♫ Spotify' : '⚡ Strava'
)

// ── Likert helpers ──────────────────────────────────────────────
const likertMax = computed(() => {
  if (!nextItem.value) return 5
  return nextItem.value.scale === 'likert_7' ? 7 : 5
})

// ── Fetch & init ────────────────────────────────────────────────
onMounted(async () => {
  pickedConnector.value = pickConnector()

  const [itemRes, profileRes] = await Promise.allSettled([
    apiFetch<NextItem | null>(`/api/psychometrics/next-item?connector=${pickedConnector.value}`),
    apiFetch<Record<string, unknown> | null>(`/api/${pickedConnector.value}/profile`),
  ])

  if (itemRes.status === 'fulfilled') nextItem.value = itemRes.value
  if (profileRes.status === 'fulfilled') connectorData.value = profileRes.value

  // If we have no data and no question, don't show
  if (!nextItem.value && !connectorData.value) {
    emit('close')
    return
  }

  // Fade in
  setTimeout(() => { visible.value = true }, 100)
})

// ── Submit ──────────────────────────────────────────────────────
async function submit(value: number) {
  if (!nextItem.value || submitting.value) return
  submitting.value = true
  selectedValue.value = value
  try {
    await apiFetch('/api/psychometrics/microdose', {
      method: 'POST',
      body: JSON.stringify({
        item_id: nextItem.value.item_id,
        value,
        connector_context: pickedConnector.value,
        trance_coherence: props.coherence,
        session_duration_ms: props.sessionDuration,
      }),
    })
    submitted.value = true
    setTimeout(() => emit('close'), 1200)
  } catch {
    submitting.value = false
  }
}

function submitCategorical(index: number) {
  submit(index)
}

function handleBackdropClick(e: MouseEvent) {
  if ((e.target as HTMLElement).classList.contains('overlay-backdrop')) {
    emit('close')
  }
}
</script>

<template>
  <div
    class="overlay-backdrop fixed inset-0 z-50 flex items-center justify-center p-4"
    :class="visible ? 'opacity-100' : 'opacity-0'"
    style="transition: opacity 1.5s ease; background: rgba(0, 0, 0, 0.4)"
    @click="handleBackdropClick"
  >
    <div
      class="overlay-card relative w-full max-w-[400px] rounded-2xl border border-white/10 p-6 space-y-5"
      :class="submitted ? 'opacity-0 translate-y-2' : 'opacity-100 translate-y-0'"
      style="
        background: rgba(15, 10, 25, 0.75);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        transition: opacity 1s ease, transform 1s ease;
      "
    >
      <!-- Close -->
      <button
        class="absolute top-3 right-3 text-gray-600 hover:text-gray-400 text-sm"
        @click="emit('close')"
      >✕</button>

      <!-- Connector data -->
      <div v-if="connectorStats.length" class="space-y-1.5">
        <div class="text-xs uppercase tracking-widest text-gray-500">{{ connectorLabel }}</div>
        <div v-for="stat in connectorStats" :key="stat.label" class="flex justify-between text-sm">
          <span class="text-gray-500">{{ stat.label }}</span>
          <span class="text-gray-300">{{ stat.value }}</span>
        </div>
      </div>

      <!-- Trance line -->
      <div class="text-xs text-gray-600 text-center">{{ tranceLine }}</div>

      <!-- Psychometric item -->
      <div v-if="nextItem" class="space-y-4">
        <p class="text-sm text-gray-200 leading-relaxed">{{ nextItem.text }}</p>

        <!-- Likert scale -->
        <div v-if="nextItem.scale !== 'categorical'" class="flex justify-center gap-1.5">
          <button
            v-for="n in likertMax"
            :key="n"
            class="w-9 h-9 rounded-lg text-sm font-medium transition-all"
            :class="
              selectedValue === n
                ? 'bg-purple-600 text-white scale-110'
                : 'bg-white/5 text-gray-400 hover:bg-white/10 hover:text-gray-200'
            "
            :disabled="submitting"
            @click="submit(n)"
          >{{ n }}</button>
        </div>

        <!-- Categorical options -->
        <div v-else class="space-y-1.5">
          <button
            v-for="(opt, idx) in nextItem.options"
            :key="opt"
            class="w-full py-2 px-3 rounded-lg text-sm text-left transition-all"
            :class="
              selectedValue === idx
                ? 'bg-purple-600 text-white'
                : 'bg-white/5 text-gray-400 hover:bg-white/10 hover:text-gray-200'
            "
            :disabled="submitting"
            @click="submitCategorical(idx)"
          >{{ opt }}</button>
        </div>

        <!-- Progress -->
        <div v-if="nextItem.progress" class="flex items-center gap-2">
          <div class="flex-1 h-0.5 bg-gray-800 rounded-full overflow-hidden">
            <div
              class="h-full bg-purple-600/50 rounded-full transition-all duration-500"
              :style="{ width: `${(nextItem.progress.answered / nextItem.progress.core_total) * 100}%` }"
            />
          </div>
          <span class="text-xs text-gray-600 tabular-nums">
            {{ nextItem.progress.answered }} / {{ nextItem.progress.core_total }}
          </span>
        </div>
      </div>

      <!-- Data-only mode (no question) -->
      <div v-else-if="connectorStats.length" class="text-center">
        <p class="text-xs text-gray-600">reflect on your signal</p>
      </div>
    </div>
  </div>
</template>
