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

      <!-- Connected sources summary -->
      <div v-if="connectedSources.length > 0" class="mt-8 bg-gray-800/50 border border-green-500/20 rounded-2xl p-5">
        <h3 class="text-sm font-medium text-green-400 uppercase tracking-wider mb-3">Connected</h3>
        <div class="flex flex-wrap gap-3">
          <div v-for="src in connectedSources" :key="src.key" class="flex items-center gap-2 text-sm text-gray-400">
            <span class="w-2 h-2 rounded-full bg-green-500"></span>
            {{ src.label }}
            <span v-if="src.lastSync" class="text-gray-600 text-xs">{{ new Date(src.lastSync).toLocaleDateString() }}</span>
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
import { computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useVibeStore } from '@/composables/useVibeStore'
import RadarIcon from '@/components/icons/RadarIcon.vue'
import SignalIcon from '@/components/icons/SignalIcon.vue'
import SpotifyConnect from '@/components/SpotifyConnect.vue'
import TwitterConnect from '@/components/TwitterConnect.vue'

const router = useRouter()
const route = useRoute()
const { oauthState, isMatchReady, markConnected } = useVibeStore()

const connectedSources = computed(() => {
  const sources: Array<{ key: string; label: string; lastSync: string | null }> = []
  if (oauthState.value.spotify.connected) sources.push({ key: 'spotify', label: 'Spotify', lastSync: oauthState.value.spotify.lastSync })
  if (oauthState.value.twitter.connected) sources.push({ key: 'twitter', label: 'X / Twitter', lastSync: oauthState.value.twitter.lastSync })
  return sources
})

// Handle return from Spotify OAuth callback
// Backend redirects to /game?spotify=connected — but we land on /calibrate first
// if the user navigates back, so also handle the param here.
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

