<template>
  <div class="min-h-screen bg-gray-900 text-gray-100 p-8 flex flex-col items-center">
    <div class="max-w-3xl w-full space-y-12">

      <div class="text-center space-y-4">
        <div class="flex items-center justify-center gap-4 mb-2">
          <RadarIcon />
          <h1 class="text-4xl font-extrabold tracking-tight text-white">Calibrate Your Vibes</h1>
          <SignalIcon />
        </div>
        <p class="text-gray-400 text-lg">
          We don't care what you look like. We care about what you listen to, what you laugh at, and how you spend your time. Connect your accounts to train the algorithm.
        </p>
      </div>

      <div class="grid grid-cols-1 gap-8">

        <!-- Spotify -->
        <div v-if="!oauthState.spotify.connected"
             class="bg-gray-800 border border-gray-700 rounded-2xl p-6 shadow-xl transition-transform hover:-translate-y-1">
          <div class="flex justify-between items-start mb-4">
            <div>
              <h2 class="text-2xl font-bold text-green-400">Spotify</h2>
              <h3 class="text-sm font-medium text-gray-500 uppercase tracking-wider mt-1">The Sonic Blueprint</h3>
            </div>
            <SpotifyConnect />
          </div>
          <div class="space-y-3 text-gray-300">
            <p><strong>Data Collected:</strong> Top artists, heavy-rotation tracks, acoustic properties (danceability, valence, tempo).</p>
            <p><strong>Correlation Engine:</strong> The sonic aesthetic is the core match catalyst. Shared obsessions with obscure 90s shoegaze or high-tempo hyperpop bump compatibility scores — the audio fingerprint becomes part of your psychological coordinate in Pinecone.</p>
          </div>
        </div>

        <!-- Twitter -->
        <div v-if="!oauthState.twitter.connected"
             class="bg-gray-800 border border-gray-700 rounded-2xl p-6 shadow-xl transition-transform hover:-translate-y-1">
          <div class="flex justify-between items-start mb-4">
            <div>
              <h2 class="text-2xl font-bold text-blue-400">X / Twitter</h2>
              <h3 class="text-sm font-medium text-gray-500 uppercase tracking-wider mt-1">The Neurotic Imprint</h3>
            </div>
            <TwitterConnect />
          </div>
          <div class="space-y-3 text-gray-300">
            <p><strong>Data Collected:</strong> Followed accounts, liked tweets, linguistic patterns, chronological posting habits.</p>
            <p><strong>Correlation Engine:</strong> Humor compatibility and ideological alignment. The LLM extracts dominance, neuroticism, and dark humor scores from your social graph to deepen the match signal.</p>
          </div>
        </div>

      </div>

      <!-- Connected sources summary + feedback -->
      <div v-if="connectedSources.length > 0" class="mt-8 bg-gray-800/50 border border-green-500/20 rounded-2xl p-5 space-y-4">
        <h3 class="text-sm font-medium text-green-400 uppercase tracking-wider">Connected</h3>
        <div class="space-y-4">
          <div v-for="src in connectedSources" :key="src.key">
            <div class="flex items-center gap-2 text-sm text-gray-400 mb-2">
              <span class="w-2 h-2 rounded-full bg-green-500"></span>
              {{ src.label }}
              <span v-if="src.lastSync" class="text-gray-600 text-xs">{{ new Date(src.lastSync).toLocaleDateString() }}</span>
            </div>

            <!-- Feedback widget -->
            <div v-if="!feedbackGiven[src.key]" class="ml-4 flex flex-col gap-2">
              <p class="text-xs text-gray-500">How useful does this feel for finding your match?</p>
              <div class="flex items-center gap-1">
                <button
                  v-for="n in 5"
                  :key="n"
                  @click="setRating(src.key, n)"
                  class="text-xl transition-transform hover:scale-110"
                  :class="(pendingRating[src.key] || 0) >= n ? 'text-yellow-400' : 'text-gray-700'"
                >★</button>
              </div>
              <div v-if="pendingRating[src.key]" class="flex flex-wrap gap-2">
                <button
                  v-for="tag in FEEDBACK_TAGS"
                  :key="tag"
                  @click="toggleTag(src.key, tag)"
                  class="text-xs px-2.5 py-1 rounded-full border transition-colors"
                  :class="selectedTags[src.key]?.includes(tag)
                    ? 'border-purple-500 text-purple-400 bg-purple-900/20'
                    : 'border-gray-700 text-gray-500 hover:border-gray-500'"
                >{{ tag.replace(/_/g, ' ') }}</button>
                <button
                  @click="submitFeedback(src.key)"
                  class="text-xs px-3 py-1 rounded-full bg-purple-700 text-white hover:bg-purple-600 transition-colors ml-auto"
                >Submit</button>
              </div>
            </div>
            <div v-else class="ml-4 text-xs text-gray-600">Thanks for the feedback ✓</div>
          </div>
        </div>
      </div>

      <div class="flex justify-center pt-6">
        <button
          :disabled="!isMatchReady"
          @click="proceed"
          class="bg-purple-600 hover:bg-purple-700 disabled:opacity-40 disabled:cursor-not-allowed text-white font-extrabold text-xl py-4 px-12 rounded-full shadow-[0_0_20px_rgba(147,51,234,0.4)] transition-all"
        >
          Generate Profile & Seek Vibes
        </button>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useVibeStore } from '@/composables/useVibeStore'
import { useAdminStore } from '@/composables/useAdminStore'
import RadarIcon from '@/components/icons/RadarIcon.vue'
import SignalIcon from '@/components/icons/SignalIcon.vue'
import SpotifyConnect from '@/components/SpotifyConnect.vue'
import TwitterConnect from '@/components/TwitterConnect.vue'

const FEEDBACK_TAGS = ['felt_relevant', 'too_invasive', 'didnt_add_value', 'surprised_me', 'want_more_like_this']

const router = useRouter()
const route = useRoute()
const { oauthState, isMatchReady, markConnected } = useVibeStore()
const { submitConnectorFeedback } = useAdminStore()

const pendingRating = reactive<Record<string, number>>({})
const selectedTags = reactive<Record<string, string[]>>({})
const feedbackGiven = reactive<Record<string, boolean>>({})

const connectedSources = computed(() => {
  const sources: Array<{ key: string; label: string; lastSync: string | null }> = []
  if (oauthState.value.spotify.connected) sources.push({ key: 'spotify', label: 'Spotify', lastSync: oauthState.value.spotify.lastSync })
  if (oauthState.value.twitter.connected) sources.push({ key: 'twitter', label: 'X / Twitter', lastSync: oauthState.value.twitter.lastSync })
  return sources
})

function setRating(provider: string, n: number) {
  pendingRating[provider] = n
  if (!selectedTags[provider]) selectedTags[provider] = []
}

function toggleTag(provider: string, tag: string) {
  if (!selectedTags[provider]) selectedTags[provider] = []
  const idx = selectedTags[provider].indexOf(tag)
  if (idx === -1) selectedTags[provider].push(tag)
  else selectedTags[provider].splice(idx, 1)
}

async function submitFeedback(provider: string) {
  const rating = pendingRating[provider]
  if (!rating) return
  try {
    await submitConnectorFeedback(provider, rating, selectedTags[provider] || [])
    feedbackGiven[provider] = true
  } catch { /* non-blocking */ }
}

onMounted(() => {
  if (route.query.spotify === 'connected') {
    markConnected('spotify')
    router.replace({ path: '/calibrate' })
  }
  if (route.query.gcal === 'connected') {
    markConnected('google')
    router.replace({ path: '/calibrate' })
  }
  if (route.query.twitter === 'connected') {
    markConnected('twitter')
    router.replace({ path: '/calibrate' })
  }
})

function proceed() {
  router.push('/game')
}
</script>

