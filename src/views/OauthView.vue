<template>
  <div class="min-h-screen bg-gray-900 text-gray-100 p-8 flex flex-col items-center">
    <div class="max-w-3xl w-full space-y-12">

      <div class="text-center space-y-4">
        <div class="flex items-center justify-center gap-4 mb-2">
          <RadarIcon />
          <h1 class="text-4xl font-extrabold tracking-tight text-white">Calibrate Your Signal</h1>
          <SignalIcon />
        </div>
        <p class="text-gray-400 text-lg">
          We don't care what you look like. We care about what you listen to, what you laugh at, and how you spend your time.
          Connect the accounts that matter — each one sharpens the signal.
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
            <p><strong>Correlation Engine:</strong> The sonic aesthetic is the core match catalyst. Shared obsessions with obscure 90s shoegaze or high-tempo hyperpop bump compatibility scores — the audio fingerprint becomes part of your psychological coordinate.</p>
          </div>
        </div>

        <!-- Twitter / X -->
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

        <!-- Strava -->
        <div class="bg-gray-800 border rounded-2xl p-6 shadow-xl transition-transform hover:-translate-y-1"
             :class="oauthState.strava.connected ? 'border-orange-500/50' : 'border-gray-700'">
          <div class="flex justify-between items-start mb-4">
            <div>
              <h2 class="text-2xl font-bold text-orange-400">Strava</h2>
              <h3 class="text-sm font-medium text-gray-500 uppercase tracking-wider mt-1">The Somatic Ledger</h3>
            </div>
            <StravaConnect />
          </div>
          <div class="space-y-3 text-gray-300">
            <p><strong>Data Collected:</strong> Heart-rate exertion curves, elevation masochism, routing patterns, recovery windows.</p>
            <p><strong>Correlation Engine:</strong> High-karma users matching on somatic data are routed into <span class="text-orange-400 font-semibold">Shared Suffering</span> co-op events — blind 5K runs ending at a partnered local brewery.</p>
          </div>
          <p class="mt-4 text-xs text-gray-600 font-mono italic">Since your body holds the tension your mind ignores.</p>
        </div>

        <!-- Google Calendar -->
        <div class="bg-gray-800 border rounded-2xl p-6 shadow-xl transition-transform hover:-translate-y-1"
             :class="oauthState.google.connected ? 'border-red-500/50' : 'border-gray-700'">
          <div class="flex justify-between items-start mb-4">
            <div>
              <h2 class="text-2xl font-bold text-red-400">Google Calendar</h2>
              <h3 class="text-sm font-medium text-gray-500 uppercase tracking-wider mt-1">The Temporal Grid</h3>
            </div>
            <GCalConnect />
          </div>
          <div class="space-y-3 text-gray-300">
            <p><strong>Data Collected:</strong> Event density, free/busy windows, recurring rituals, peak scheduling hours, evening overcommitment ratio.</p>
            <p><strong>Correlation Engine:</strong> Maps your <span class="text-red-400 font-semibold">Temporal Anxiety</span> — when you overbook, when you leave white space, and whether your calendar reflects intention or dread. The Oracle uses this to predict burnout compatibility and co-regulation windows.</p>
          </div>
          <p class="mt-4 text-xs text-gray-600 font-mono italic">Your schedule is a confession you write every morning.</p>
        </div>

        <!-- Co-Star -->
        <div class="bg-gray-800 border rounded-2xl p-6 shadow-xl transition-transform hover:-translate-y-1"
             :class="oauthState.costar.connected ? 'border-indigo-500/50' : 'border-gray-700'">
          <div class="flex justify-between items-start mb-4">
            <div>
              <h2 class="text-2xl font-bold text-indigo-400">Co&#8239;&#8212;&#8239;Star</h2>
              <h3 class="text-sm font-medium text-gray-500 uppercase tracking-wider mt-1">The Fatalistic Mirror</h3>
            </div>
            <CoStarConnect />
          </div>
          <div class="space-y-3 text-gray-300">
            <p><strong>Data Collected:</strong> Full natal chart (Sun, Moon, Rising, Mars, Venus), check-in frequency, transit anxiety correlation.</p>
            <p><strong>Correlation Engine:</strong> The Oracle uses your chart to predict friction points and structure daily challenges. Pseudo-science becomes an engine for genuine generosity.</p>
          </div>
          <p class="mt-4 text-xs text-gray-600 font-mono italic">Since you already look to the void for answers.</p>
        </div>

        <!-- Letterboxd -->
        <div class="bg-gray-800 border rounded-2xl p-6 shadow-xl transition-transform hover:-translate-y-1"
             :class="oauthState.letterboxd.connected ? 'border-emerald-500/50' : 'border-gray-700'">
          <div class="flex justify-between items-start mb-4">
            <div>
              <h2 class="text-2xl font-bold text-emerald-400">Letterboxd</h2>
              <h3 class="text-sm font-medium text-gray-500 uppercase tracking-wider mt-1">The Empathy Simulator</h3>
            </div>
            <LetterboxdConnect />
          </div>
          <div class="space-y-3 text-gray-300">
            <p><strong>Data Collected:</strong> Watchlist, diary entries, star ratings, aesthetic pretension markers.</p>
            <p><strong>Correlation Engine:</strong> Unlocks the <span class="text-emerald-400 font-semibold">Cinema Co-Op</span>. Matches are routed to partnered indie theaters — ticket discounts scale with the obscurity of your shared watchlist.</p>
          </div>
          <p class="mt-4 text-xs text-gray-600 font-mono italic">We already know you cried during that one.</p>
        </div>

        <!-- Steam -->
        <div class="bg-gray-800 border rounded-2xl p-6 shadow-xl transition-transform hover:-translate-y-1"
             :class="oauthState.steam.connected ? 'border-blue-500/50' : 'border-gray-700'">
          <div class="flex justify-between items-start mb-4">
            <div>
              <h2 class="text-2xl font-bold text-blue-400">Steam</h2>
              <h3 class="text-sm font-medium text-gray-500 uppercase tracking-wider mt-1">The Isolation Metric</h3>
            </div>
            <SteamConnect />
          </div>
          <div class="space-y-3 text-gray-300">
            <p><strong>Data Collected:</strong> Recently played games, total hours logged, single-player vs. co-op ratio, late-night session frequency.</p>
            <p><strong>Correlation Engine:</strong> Maps async isolation hours and cooperative tendencies. High-anxiety users are eased into digital hangouts before the algorithm deploys them into the physical world.</p>
          </div>
          <p class="mt-4 text-xs text-gray-600 font-mono italic">80 hours in Skyrim this fortnight. We see you. We're routing you gently.</p>
        </div>

      </div>

      <!-- Connected sources + feedback -->
      <div v-if="connectedSources.length > 0" class="mt-8 bg-gray-800/50 border border-green-500/20 rounded-2xl p-5 space-y-4">
        <h3 class="text-sm font-medium text-green-400 uppercase tracking-wider">Connected</h3>
        <div class="space-y-4">
          <div v-for="src in connectedSources" :key="src.key">
            <div class="flex items-center gap-2 text-sm text-gray-400 mb-2">
              <span class="w-2 h-2 rounded-full bg-green-500"></span>
              {{ src.label }}
              <span v-if="src.lastSync" class="text-gray-600 text-xs">{{ new Date(src.lastSync).toLocaleDateString() }}</span>
            </div>

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
            <div v-else class="ml-4 text-xs text-gray-600">Feedback recorded ✓</div>
          </div>
        </div>
      </div>

      <!-- CTA -->
      <div class="flex flex-col items-center gap-4 pt-6">
        <button
          @click="proceed"
          class="bg-purple-600 hover:bg-purple-700 text-white font-extrabold text-xl py-4 px-12 rounded-full shadow-[0_0_20px_rgba(147,51,234,0.4)] transition-all"
        >
          Enter the Field
        </button>
        <p class="text-gray-600 text-sm font-mono text-center max-w-sm">
          Connections deepen the signal over time — you can always return here to add more.
        </p>
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
import StravaConnect from '@/components/StravaConnect.vue'
import CoStarConnect from '@/components/CoStarConnect.vue'
import LetterboxdConnect from '@/components/LetterboxdConnect.vue'
import SteamConnect from '@/components/SteamConnect.vue'
import GCalConnect from '@/components/GCalConnect.vue'

const FEEDBACK_TAGS = ['felt_relevant', 'didnt_add_value', 'surprised_me', 'want_more_like_this']

const router = useRouter()
const route = useRoute()
const { oauthState, markConnected } = useVibeStore()
const { submitConnectorFeedback } = useAdminStore()

const pendingRating = reactive<Record<string, number>>({})
const selectedTags = reactive<Record<string, string[]>>({})
const feedbackGiven = reactive<Record<string, boolean>>({})

const connectedSources = computed(() => {
  const all = [
    { key: 'spotify',    label: 'Spotify',     state: oauthState.value.spotify },
    { key: 'twitter',    label: 'X / Twitter',  state: oauthState.value.twitter },
    { key: 'strava',     label: 'Strava',       state: oauthState.value.strava },
    { key: 'google',     label: 'Google Calendar', state: oauthState.value.google },
    { key: 'costar',     label: 'Co-Star',      state: oauthState.value.costar },
    { key: 'letterboxd', label: 'Letterboxd',   state: oauthState.value.letterboxd },
    { key: 'steam',      label: 'Steam',        state: oauthState.value.steam },
  ]
  return all
    .filter(s => s.state.connected)
    .map(s => ({ key: s.key, label: s.label, lastSync: s.state.lastSync }))
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
  feedbackGiven[provider] = true  // close immediately regardless of API result
  try {
    await submitConnectorFeedback(provider, rating, selectedTags[provider] || [])
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
  if (route.query.steam === 'connected') {
    markConnected('steam')
    router.replace({ path: '/calibrate' })
  }
  if (route.query.strava === 'connected') {
    markConnected('strava')
    router.replace({ path: '/calibrate' })
  }
})

function proceed() {
  router.push('/intake')
}
</script>
