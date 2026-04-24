<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useRevealStore } from '@/composables/useRevealStore'
import AuraField from '@/components/AuraField.vue'
import PairedBar from '@/components/PairedBar.vue'

const router = useRouter()
const route = useRoute()
const matchId = route.params.matchId as string
const { fetchReveal, revealData, revealLoading, revealError } = useRevealStore()

// Intersection observer for scroll animations
const visibleSections = ref<Set<string>>(new Set())
let observer: IntersectionObserver | null = null

function setupObserver() {
  observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        const id = (entry.target as HTMLElement).dataset.section
        if (!id) return
        if (entry.isIntersecting) visibleSections.value.add(id)
      })
    },
    { threshold: 0.15 },
  )
  document.querySelectorAll('[data-section]').forEach((el) => observer!.observe(el))
}

onMounted(async () => {
  await fetchReveal(matchId)
  if (revealError.value) return

  // Check if fitting is complete — redirect if not
  if (revealData.value && !revealData.value.self?.fitting_self) {
    router.replace(`/fitting/${matchId}`)
    return
  }

  // Setup observer after data loads
  setTimeout(setupObserver, 100)
})

onUnmounted(() => observer?.disconnect())

// ── Desire overlap helpers ──────────────────────────────────
function proximity(a: number, b: number, range: number): number {
  return Math.round((1 - Math.abs(a - b) / range) * 100)
}

function skinDistance(a: string, b: string): string {
  const hexToRgb = (hex: string) => {
    const r = parseInt(hex.slice(1, 3), 16)
    const g = parseInt(hex.slice(3, 5), 16)
    const bl = parseInt(hex.slice(5, 7), 16)
    return [r, g, bl]
  }
  const [r1, g1, b1] = hexToRgb(a)
  const [r2, g2, b2] = hexToRgb(b)
  const dist = Math.sqrt((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2)
  if (dist < 80) return 'close'
  if (dist < 160) return 'moderate'
  return 'different'
}

const bigFiveLabels: Record<string, string> = {
  O: 'Openness', C: 'Conscientiousness', E: 'Extraversion',
  A: 'Agreeableness', N: 'Neuroticism',
}
</script>

<template>
  <div class="min-h-screen bg-gray-950 text-gray-100">
    <!-- Loading -->
    <div v-if="revealLoading" class="flex items-center justify-center h-screen">
      <div class="text-gray-500">Loading signal story...</div>
    </div>

    <!-- Error -->
    <div v-else-if="revealError" class="flex flex-col items-center justify-center h-screen gap-4">
      <div class="text-red-400">{{ revealError }}</div>
      <button @click="router.push('/game')" class="text-sm text-gray-500 hover:text-white">Back to matches</button>
    </div>

    <!-- Reveal scroll -->
    <div v-else-if="revealData" class="max-w-4xl mx-auto px-6 py-16 space-y-32">

      <!-- Section 1: Signal Silhouettes -->
      <section
        data-section="silhouettes"
        class="min-h-[70vh] flex flex-col items-center justify-center transition-all duration-700"
        :class="visibleSections.has('silhouettes') ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'"
      >
        <h2 class="text-xs uppercase tracking-widest text-gray-500 mb-12">Signal Silhouettes</h2>
        <div class="flex items-center gap-12 lg:gap-24">
          <div class="text-center">
            <AuraField
              :fitting="revealData.self?.fitting_self ?? null"
              :has-spotify="revealData.self?.has_spotify ?? false"
              :has-oracle="revealData.self?.has_oracle ?? false"
              :has-psychometric="!!revealData.psychometrics?.self"
              :has-activity="(revealData.self?.has_strava ?? false) || (revealData.self?.has_steam ?? false)"
              :has-attachment="!!revealData.self?.attachment_style"
            />
            <div class="text-sm text-gray-400 mt-4">You</div>
          </div>
          <div class="text-center">
            <AuraField
              :fitting="revealData.match?.fitting_self ?? null"
              :has-spotify="revealData.match?.has_spotify ?? false"
              :has-oracle="revealData.match?.has_oracle ?? false"
              :has-psychometric="!!revealData.psychometrics?.match"
              :has-activity="(revealData.match?.has_strava ?? false) || (revealData.match?.has_steam ?? false)"
              :has-attachment="!!revealData.match?.attachment_style"
            />
            <div class="text-sm text-gray-400 mt-4">{{ revealData.match?.display_name || 'Your match' }}</div>
          </div>
        </div>
      </section>

      <!-- Section 2: Desire Overlap -->
      <section
        v-if="revealData.self?.fitting_ideal && revealData.match?.fitting_self"
        data-section="desire"
        class="transition-all duration-700"
        :class="visibleSections.has('desire') ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'"
      >
        <h2 class="text-xs uppercase tracking-widest text-gray-500 mb-8 text-center">Desire Overlap</h2>
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <!-- What you imagined vs Who they are -->
          <div class="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <h3 class="text-sm text-gray-400 mb-4">What you imagined → Who they are</h3>
            <div class="space-y-2 text-sm">
              <div class="flex justify-between">
                <span class="text-gray-500">Body type</span>
                <span :class="revealData.self.fitting_ideal.body_type === revealData.match.fitting_self.body_type ? 'text-green-400' : 'text-gray-600'">
                  {{ revealData.self.fitting_ideal.body_type === revealData.match.fitting_self.body_type ? '✓ Match' : '✗ Different' }}
                </span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-500">Build proximity</span>
                <span class="text-purple-400">{{ proximity(revealData.self.fitting_ideal.build, revealData.match.fitting_self.build, 9) }}%</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-500">Height proximity</span>
                <span class="text-purple-400">{{ proximity(revealData.self.fitting_ideal.height, revealData.match.fitting_self.height, 26) }}%</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-500">Coloring</span>
                <span class="text-purple-400">{{ skinDistance(revealData.self.fitting_ideal.skin_color, revealData.match.fitting_self.skin_color) }}</span>
              </div>
            </div>
          </div>
          <!-- What they imagined vs Who you are -->
          <div v-if="revealData.match?.fitting_ideal && revealData.self?.fitting_self" class="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <h3 class="text-sm text-gray-400 mb-4">What they imagined → Who you are</h3>
            <div class="space-y-2 text-sm">
              <div class="flex justify-between">
                <span class="text-gray-500">Body type</span>
                <span :class="revealData.match.fitting_ideal.body_type === revealData.self.fitting_self.body_type ? 'text-green-400' : 'text-gray-600'">
                  {{ revealData.match.fitting_ideal.body_type === revealData.self.fitting_self.body_type ? '✓ Match' : '✗ Different' }}
                </span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-500">Build proximity</span>
                <span class="text-pink-400">{{ proximity(revealData.match.fitting_ideal.build, revealData.self.fitting_self.build, 9) }}%</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-500">Height proximity</span>
                <span class="text-pink-400">{{ proximity(revealData.match.fitting_ideal.height, revealData.self.fitting_self.height, 26) }}%</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-500">Coloring</span>
                <span class="text-pink-400">{{ skinDistance(revealData.match.fitting_ideal.skin_color, revealData.self.fitting_self.skin_color) }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Section 3: Signal Layers -->
      <section
        data-section="signals"
        class="transition-all duration-700"
        :class="visibleSections.has('signals') ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'"
      >
        <h2 class="text-xs uppercase tracking-widest text-gray-500 mb-8 text-center">Signal Layers</h2>
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">

          <!-- Spotify -->
          <div v-if="revealData.self?.has_spotify && revealData.match?.has_spotify" class="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <h3 class="text-sm font-medium text-green-400 mb-4">♫ Spotify</h3>
            <div v-if="revealData.self.spotify_data && revealData.match.spotify_data">
              <div class="flex flex-wrap gap-1 mb-3">
                <span
                  v-for="g in (revealData!.self!.spotify_data as any).genres?.filter((g: string) => (revealData!.match!.spotify_data as any)?.genres?.includes(g))?.slice(0, 5) ?? []"
                  :key="g"
                  class="text-xs px-2 py-0.5 bg-green-900/30 text-green-400 rounded-full"
                >{{ g }}</span>
                <span v-if="!(revealData!.self!.spotify_data as any).genres?.some((g: string) => (revealData!.match!.spotify_data as any)?.genres?.includes(g))" class="text-xs text-gray-600">No shared genres</span>
              </div>
              <div class="space-y-1.5">
                <PairedBar
                  label="Valence"
                  :self-value="(revealData.self.spotify_data as any)?.audio_avg?.valence ?? 0"
                  :match-value="(revealData.match.spotify_data as any)?.audio_avg?.valence ?? 0"
                  self-color="#22C55E"
                  match-color="#86EFAC"
                />
                <PairedBar
                  label="Energy"
                  :self-value="(revealData.self.spotify_data as any)?.audio_avg?.energy ?? 0"
                  :match-value="(revealData.match.spotify_data as any)?.audio_avg?.energy ?? 0"
                  self-color="#EF4444"
                  match-color="#FCA5A5"
                />
                <PairedBar
                  label="Danceability"
                  :self-value="(revealData.self.spotify_data as any)?.audio_avg?.danceability ?? 0"
                  :match-value="(revealData.match.spotify_data as any)?.audio_avg?.danceability ?? 0"
                  self-color="#22C55E"
                  match-color="#86EFAC"
                />
              </div>
            </div>
          </div>

          <!-- Oracle -->
          <div v-if="revealData.self?.has_oracle && revealData.match?.has_oracle" class="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <h3 class="text-sm font-medium text-pink-400 mb-4">☿ Oracle</h3>
            <div class="space-y-1.5 mb-4">
              <PairedBar
                v-for="key in ['empathy_index', 'isolation_metric', 'fatalism_score', 'masochism_curve']"
                :key="key"
                :label="key.replace(/_/g, ' ')"
                :self-value="(revealData.self?.oracle_coordinate as any)?.[key] ?? 0"
                :match-value="(revealData.match?.oracle_coordinate as any)?.[key] ?? 0"
                self-color="#EC4899"
                match-color="#F9A8D4"
              />
            </div>
            <p v-if="(revealData.match?.oracle_coordinate as any)?.oracle_rationale" class="text-xs text-gray-500 leading-relaxed italic">
              "{{ (revealData.match.oracle_coordinate as any).oracle_rationale }}"
            </p>
          </div>

          <!-- Strava -->
          <div v-if="revealData.self?.has_strava && revealData.match?.has_strava" class="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <h3 class="text-sm font-medium text-blue-400 mb-4">⚡ Strava</h3>
            <div class="flex flex-wrap gap-1">
              <span
                v-for="a in (revealData!.self?.strava_data as any)?.activity_types?.filter((t: string) => (revealData!.match?.strava_data as any)?.activity_types?.includes(t)) ?? []"
                :key="a"
                class="text-xs px-2 py-0.5 bg-blue-900/30 text-blue-400 rounded-full"
              >{{ a }}</span>
              <span class="text-xs text-gray-600 ml-1">shared activities</span>
            </div>
          </div>

          <!-- No shared signals fallback -->
          <div
            v-if="!revealData.self?.has_spotify && !revealData.self?.has_oracle && !revealData.self?.has_strava"
            class="bg-gray-900 border border-gray-800 rounded-xl p-6 text-center col-span-full"
          >
            <p class="text-sm text-gray-500">Connect more signals to enrich your match story</p>
            <router-link to="/calibrate" class="text-xs text-purple-400 hover:text-purple-300 mt-2 inline-block">Go to calibrate →</router-link>
          </div>
        </div>
      </section>

      <!-- Section 4: Psychometric Alignment -->
      <section
        v-if="revealData.psychometrics?.self && revealData.psychometrics?.match"
        data-section="psychometrics"
        class="transition-all duration-700"
        :class="visibleSections.has('psychometrics') ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'"
      >
        <h2 class="text-xs uppercase tracking-widest text-gray-500 mb-8 text-center">Psychometric Alignment</h2>
        <div class="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
          <!-- Big Five -->
          <div v-if="revealData.psychometrics.self.ipip_neo_scores && revealData.psychometrics.match.ipip_neo_scores">
            <h3 class="text-xs text-gray-500 uppercase tracking-wider mb-3">Big Five</h3>
            <div class="space-y-2">
              <PairedBar
                v-for="(label, key) in bigFiveLabels"
                :key="key"
                :label="label"
                :self-value="revealData.psychometrics.self.ipip_neo_scores[key] ?? 0"
                :match-value="revealData.psychometrics.match.ipip_neo_scores[key] ?? 0"
              />
            </div>
          </div>

          <!-- ECR-R -->
          <div v-if="revealData.psychometrics.self.ecr_r_scores && revealData.psychometrics.match.ecr_r_scores">
            <h3 class="text-xs text-gray-500 uppercase tracking-wider mb-3 mt-6">Attachment Dimensions</h3>
            <div class="space-y-2">
              <PairedBar
                label="Anxiety"
                :self-value="revealData.psychometrics.self.ecr_r_scores.anxiety ?? 0"
                :match-value="revealData.psychometrics.match.ecr_r_scores.anxiety ?? 0"
              />
              <PairedBar
                label="Avoidance"
                :self-value="revealData.psychometrics.self.ecr_r_scores.avoidance ?? 0"
                :match-value="revealData.psychometrics.match.ecr_r_scores.avoidance ?? 0"
              />
            </div>
          </div>

          <!-- Pill badges -->
          <div class="flex flex-wrap gap-2 mt-4">
            <template v-for="field in ['love_language', 'values_cluster', 'sociosexual_orientation'] as const" :key="field">
              <div v-if="revealData.psychometrics.self[field] || revealData.psychometrics.match[field]" class="flex gap-1">
                <span
                  v-if="revealData.psychometrics.self[field]"
                  class="text-xs px-2 py-0.5 rounded-full"
                  :class="revealData.psychometrics.self[field] === revealData.psychometrics.match[field]
                    ? 'bg-purple-900/40 text-purple-300 ring-1 ring-purple-500/50'
                    : 'bg-gray-800 text-gray-400'"
                >{{ revealData.psychometrics.self[field] }}</span>
                <span
                  v-if="revealData.psychometrics.match[field] && revealData.psychometrics.match[field] !== revealData.psychometrics.self[field]"
                  class="text-xs px-2 py-0.5 bg-gray-800 text-gray-400 rounded-full"
                >{{ revealData.psychometrics.match[field] }}</span>
              </div>
            </template>
          </div>
        </div>

        <!-- Missing psychometrics -->
        <div v-if="!revealData.psychometrics?.self" class="bg-gray-900 border border-gray-800 rounded-xl p-6 text-center">
          <p class="text-sm text-gray-500">Complete your psychometric assessment to unlock this layer</p>
          <router-link to="/psychoanalysis" class="text-xs text-purple-400 hover:text-purple-300 mt-2 inline-block">Take assessment →</router-link>
        </div>
      </section>

      <!-- Section 5: Connect -->
      <section
        data-section="connect"
        class="min-h-[50vh] flex flex-col items-center justify-center transition-all duration-700"
        :class="visibleSections.has('connect') ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'"
      >
        <div class="text-7xl font-bold text-white mb-4">
          {{ Math.round(revealData.similarity * 100) }}<span class="text-3xl text-gray-500">%</span>
        </div>
        <p class="text-sm text-gray-400 max-w-md text-center mb-8">{{ revealData.match_reason }}</p>
        <button
          @click="router.push(`/messages/${matchId}`)"
          class="px-8 py-3 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-medium transition-colors"
        >Send a message</button>
        <router-link to="/game" class="text-xs text-gray-500 hover:text-gray-400 mt-4">Back to matches</router-link>
      </section>
    </div>
  </div>
</template>
