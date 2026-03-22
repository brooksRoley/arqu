<template>
  <div class="min-h-screen bg-gray-900 text-gray-100 p-8 flex flex-col items-center">
    <div class="max-w-3xl w-full space-y-12">

      <div class="text-center space-y-4">
        <h1 class="text-4xl font-extrabold tracking-tight text-white">Calibrate Your Vibes</h1>
        <p class="text-gray-400 text-lg">
          We don't care what you look like. We care about what you listen to, what you laugh at, and how you spend your time. Connect your accounts to train the algorithm.
        </p>
      </div>

      <div class="grid grid-cols-1 gap-8">

        <!-- Spotify -->
        <div class="bg-gray-800 border rounded-2xl p-6 shadow-xl transition-transform hover:-translate-y-1"
             :class="oauthState.spotify.connected ? 'border-green-500/50' : 'border-gray-700'">
          <div class="flex justify-between items-start mb-4">
            <div>
              <h2 class="text-2xl font-bold text-green-400">Spotify</h2>
              <h3 class="text-sm font-medium text-gray-500 uppercase tracking-wider mt-1">The Sonic Blueprint</h3>
            </div>
            <button
              @click="connectSpotify"
              :disabled="oauthState.spotify.connected"
              class="font-bold py-2 px-6 rounded-full transition-colors disabled:cursor-default"
              :class="oauthState.spotify.connected
                ? 'bg-green-900 text-green-400 border border-green-500/40'
                : 'bg-green-500 hover:bg-green-600 text-gray-900'"
            >
              {{ oauthState.spotify.connected ? '✓ Connected' : 'Connect' }}
            </button>
          </div>
          <div class="space-y-3 text-gray-300">
            <p><strong>Data Collected:</strong> Top artists, heavy-rotation tracks, acoustic properties (danceability, valence, tempo).</p>
            <p><strong>Correlation Engine:</strong> The sonic aesthetic is the core match catalyst. Shared obsessions with obscure 90s shoegaze or high-tempo hyperpop bump compatibility scores — the audio fingerprint becomes part of your psychological coordinate in Pinecone.</p>
          </div>
          <p v-if="oauthState.spotify.lastSync" class="mt-3 text-xs text-gray-600">
            Last synced {{ new Date(oauthState.spotify.lastSync).toLocaleString() }}
          </p>
        </div>

        <!-- Twitter -->
        <div class="bg-gray-800 border border-gray-700/50 rounded-2xl p-6 shadow-xl opacity-60">
          <div class="flex justify-between items-start mb-4">
            <div>
              <h2 class="text-2xl font-bold text-blue-400">X / Twitter</h2>
              <h3 class="text-sm font-medium text-gray-500 uppercase tracking-wider mt-1">The Neurotic Imprint</h3>
            </div>
            <span class="text-xs text-gray-500 border border-gray-700 rounded-full px-4 py-2">Coming soon</span>
          </div>
          <div class="space-y-3 text-gray-400">
            <p><strong>Data Collected:</strong> Followed accounts, liked tweets, linguistic patterns, chronological posting habits.</p>
            <p><strong>Correlation Engine:</strong> Humor compatibility and ideological alignment. The LLM extracts dominance, neuroticism, and dark humor scores from your social graph to deepen the match signal.</p>
          </div>
        </div>

        <!-- Google Calendar -->
        <div class="bg-gray-800 border border-gray-700/50 rounded-2xl p-6 shadow-xl opacity-60">
          <div class="flex justify-between items-start mb-4">
            <div>
              <h2 class="text-2xl font-bold text-red-400">Google Calendar</h2>
              <h3 class="text-sm font-medium text-gray-500 uppercase tracking-wider mt-1">The Temporal Logistics</h3>
            </div>
            <span class="text-xs text-gray-500 border border-gray-700 rounded-full px-4 py-2">Coming soon</span>
          </div>
          <div class="space-y-3 text-gray-400">
            <p><strong>Data Collected:</strong> Free blocks of time, routine commitments, location constraints.</p>
            <p><strong>Correlation Engine:</strong> Zero-friction meetups. Once a vibe match occurs, the app cross-references calendars and queries local APIs for live events during mutually available windows — a single curated itinerary, bypassing the "when are you free" phase entirely.</p>
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
import { onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useVibeStore } from '@/composables/useVibeStore'

const router = useRouter()
const route = useRoute()
const { oauthState, isMatchReady, connectSpotify, markConnected } = useVibeStore()

// Handle return from Spotify OAuth callback
// Backend redirects to /game?spotify=connected — but we land on /calibrate first
// if the user navigates back, so also handle the param here.
onMounted(() => {
  if (route.query.spotify === 'connected') {
    markConnected('spotify')
    // Clean the query param from the URL without a full navigation
    router.replace({ path: '/calibrate' })
  }
})

function proceed() {
  router.push('/game')
}
</script>
