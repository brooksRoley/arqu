<template>
  <div class="min-h-screen bg-gray-900 text-gray-100 p-8 flex flex-col items-center">
    <div class="max-w-3xl w-full space-y-12">

      <div class="text-center space-y-4">
        <div class="flex items-center justify-center gap-4 mb-2">
          <RadarIcon color="#f97316" />
          <h1 class="text-4xl font-extrabold tracking-tight text-white">Peripheral Sync</h1>
          <SignalIcon color="#f97316" />
        </div>
        <p class="text-gray-400 text-lg">
          The core calibration mapped your taste. Now we map the rest —
          your body, your fatalism, your empathy threshold, and the hours you spend alone.
        </p>
        <p class="text-gray-600 text-sm font-mono">
          Every vector sharpens the signal. Every refusal is noted.
        </p>
      </div>

      <div class="grid grid-cols-1 gap-8">

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
            <p>
              <strong>Data Collected:</strong> Heart-rate exertion curves, elevation masochism,
              routing patterns, recovery windows.
            </p>
            <p>
              <strong>Correlation Engine:</strong> High-karma users matching on somatic data
              are routed into <span class="text-orange-400 font-semibold">Shared Suffering</span>
              co-op events — blind 5K runs ending at a partnered local brewery.
              Endorphin bonding, gamified.
            </p>
          </div>
          <p class="mt-4 text-xs text-gray-600 font-mono italic">
            Since your body holds the tension your mind ignores, sync your somatic ledger.
          </p>
          <p v-if="oauthState.strava.lastSync" class="mt-2 text-xs text-gray-600">
            Last synced {{ new Date(oauthState.strava.lastSync).toLocaleString() }}
          </p>
        </div>

        <!-- Co—Star -->
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
            <p>
              <strong>Data Collected:</strong> Full natal chart (Sun, Moon, Rising, Mars, Venus),
              check-in frequency, transit anxiety correlation.
            </p>
            <p>
              <strong>Correlation Engine:</strong> Async psychoanalysis. The Oracle uses your chart
              to predict friction points in a daily game.
              <span class="text-indigo-400 font-semibold italic">
                "Your Mars is in Scorpio. Chip in $5 for a stranger's coffee to offset your aggressive transit."
              </span>
              Pseudo-science becomes an engine for financial generosity.
            </p>
          </div>
          <p class="mt-4 text-xs text-gray-600 font-mono italic">
            Since you already look to the void for answers, let us read the constellations of your neuroticism.
          </p>
          <p v-if="oauthState.costar.lastSync" class="mt-2 text-xs text-gray-600">
            Last synced {{ new Date(oauthState.costar.lastSync).toLocaleString() }}
          </p>
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
            <p>
              <strong>Data Collected:</strong> Watchlist, diary entries, star ratings,
              aesthetic pretension markers (A24 Horror, French New Wave, Tarkovsky phase detection).
            </p>
            <p>
              <strong>Correlation Engine:</strong> Unlocks the
              <span class="text-emerald-400 font-semibold">Cinema Co-Op</span>.
              Matches are routed to partnered indie theaters — ticket discounts scale
              with the obscurity of your shared watchlist.
            </p>
          </div>
          <p class="mt-4 text-xs text-gray-600 font-mono italic">
            We already know you cried during that one. Now quantify it.
          </p>
          <p v-if="oauthState.letterboxd.lastSync" class="mt-2 text-xs text-gray-600">
            Last synced {{ new Date(oauthState.letterboxd.lastSync).toLocaleString() }}
          </p>
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
            <p>
              <strong>Data Collected:</strong> Recently played games, total hours logged,
              single-player vs. co-op ratio, late-night session frequency.
            </p>
            <p>
              <strong>Correlation Engine:</strong> Maps async isolation hours and cooperative
              tendencies. High-anxiety users are facilitated into
              <span class="text-blue-400 font-semibold">digital hangouts</span>
              before the algorithm deploys them into the physical world.
            </p>
          </div>
          <p class="mt-4 text-xs text-gray-600 font-mono italic">
            80 hours in Skyrim this fortnight. We see you. We understand. We're routing you gently.
          </p>
          <p v-if="oauthState.steam.lastSync" class="mt-2 text-xs text-gray-600">
            Last synced {{ new Date(oauthState.steam.lastSync).toLocaleString() }}
          </p>
        </div>

      </div>

      <div class="flex flex-col items-center gap-4 pt-6">
        <button
          @click="proceed"
          :disabled="synthesizing"
          class="bg-purple-600 hover:bg-purple-700 disabled:opacity-60 disabled:cursor-wait text-white font-extrabold text-xl py-4 px-12 rounded-full shadow-[0_0_20px_rgba(147,51,234,0.4)] transition-all"
        >
          {{ synthesizing ? 'The Oracle is listening...' : 'Deepen the Signal' }}
        </button>
        <button
          @click="skip"
          class="text-gray-600 hover:text-gray-400 font-mono text-sm transition-colors"
        >
          skip — the algorithm will remember this
        </button>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useVibeStore } from '@/composables/useVibeStore'
import RadarIcon from '@/components/icons/RadarIcon.vue'
import SignalIcon from '@/components/icons/SignalIcon.vue'
import StravaConnect from '@/components/StravaConnect.vue'
import CoStarConnect from '@/components/CoStarConnect.vue'
import LetterboxdConnect from '@/components/LetterboxdConnect.vue'
import SteamConnect from '@/components/SteamConnect.vue'

const router = useRouter()
const { oauthState, triggerSynthesis } = useVibeStore()
const synthesizing = ref(false)

async function proceed() {
  synthesizing.value = true
  try {
    await triggerSynthesis()
  } catch (e) {
    console.error('Oracle synthesis request failed:', e)
  }
  // Navigate regardless — synthesis runs as background task on backend
  router.push('/game')
}

function skip() {
  router.push('/game')
}
</script>
