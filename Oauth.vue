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
        
        <div class="bg-gray-800 border border-gray-700 rounded-2xl p-6 shadow-xl transition-transform hover:-translate-y-1">
          <div class="flex justify-between items-start mb-4">
            <div>
              <h2 class="text-2xl font-bold text-green-400">Spotify</h2>
              <h3 class="text-sm font-medium text-gray-500 uppercase tracking-wider mt-1">The Sonic Blueprint</h3>
            </div>
            <button @click="connectOAuth('spotify')" class="bg-green-500 hover:bg-green-600 text-gray-900 font-bold py-2 px-6 rounded-full transition-colors">
              {{ connected.spotify ? 'Connected' : 'Connect' }}
            </button>
          </div>
          <div class="space-y-3 text-gray-300">
            <p><strong>Data Collected:</strong> Top artists, heavy-rotation tracks, acoustic properties (danceability, valence, tempo), and saved playlists.</p>
            <p><strong>Correlation Engine:</strong> This is the core match catalyst. The LLM analyzes your sonic aesthetic to pair you with users who share your emotional frequency. A shared obsession with obscure 90s shoegaze or high-tempo hyperpop instantly bumps compatibility scores, dictating initial chat prompts based on overlapping audio-scapes.</p>
          </div>
        </div>

        <div class="bg-gray-800 border border-gray-700 rounded-2xl p-6 shadow-xl transition-transform hover:-translate-y-1">
          <div class="flex justify-between items-start mb-4">
            <div>
              <h2 class="text-2xl font-bold text-blue-400">X / Twitter</h2>
              <h3 class="text-sm font-medium text-gray-500 uppercase tracking-wider mt-1">The Neurotic Imprint</h3>
            </div>
            <button @click="connectOAuth('twitter')" class="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-6 rounded-full transition-colors">
              {{ connected.twitter ? 'Connected' : 'Connect' }}
            </button>
          </div>
          <div class="space-y-3 text-gray-300">
            <p><strong>Data Collected:</strong> Followed accounts, liked tweets, linguistic patterns, and chronological posting habits.</p>
            <p><strong>Correlation Engine:</strong> This dictates humor compatibility and ideological alignment. The LLM processes your social graph to ensure you aren't matched with someone whose fundamental worldview clashes with yours. It feeds directly into the "who pays" metric; the algorithm assesses dominance, generosity, and financial-social cues from your linguistic footprint to suggest tab-splitting dynamics before the date even starts.</p>
          </div>
        </div>

        <div class="bg-gray-800 border border-gray-700 rounded-2xl p-6 shadow-xl transition-transform hover:-translate-y-1">
          <div class="flex justify-between items-start mb-4">
            <div>
              <h2 class="text-2xl font-bold text-red-400">Google Calendar</h2>
              <h3 class="text-sm font-medium text-gray-500 uppercase tracking-wider mt-1">The Temporal Logistics</h3>
            </div>
            <button @click="connectOAuth('google')" class="bg-red-500 hover:bg-red-600 text-white font-bold py-2 px-6 rounded-full transition-colors">
              {{ connected.google ? 'Connected' : 'Connect' }}
            </button>
          </div>
          <div class="space-y-3 text-gray-300">
            <p><strong>Data Collected:</strong> Free blocks of time, routine commitments, and location constraints.</p>
            <p><strong>Correlation Engine:</strong> Zero-friction meetups. Once a vibe match occurs, the app cross-references your calendar with theirs and instantly queries local APIs for comedy shows, theater picks, or live music happening nearby during your mutually available windows. It generates a single, highly curated itinerary for the shared hangout, entirely bypassing the exhausting "when are you free" phase.</p>
          </div>
        </div>

      </div>
      
      <div class="flex justify-center pt-6">
        <button 
          :disabled="!canProceed"
          class="bg-purple-600 hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-extrabold text-xl py-4 px-12 rounded-full shadow-[0_0_20px_rgba(147,51,234,0.4)] transition-all"
        >
          Generate Profile & Seek Vibes
        </button>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';

const connected = ref({
  spotify: false,
  twitter: false,
  google: false
});

// Mock OAuth trigger
const connectOAuth = (provider) => {
  // In reality, this redirects to the OAuth flow for the specific provider
  console.log(`Initiating OAuth for ${provider}...`);
  
  // Simulating successful connection after a brief delay
  setTimeout(() => {
    connected.value[provider] = true;
  }, 800);
};

// Require at least Spotify to proceed, since it's a music-based app
const canProceed = computed(() => {
  return connected.value.spotify;
});
</script>