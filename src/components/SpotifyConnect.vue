<template>
  <div class="relative group w-full">
    <div
      class="absolute -inset-0.5 bg-gradient-to-r from-green-600/40 to-emerald-500/40 rounded-xl blur opacity-30 group-hover:opacity-70 transition duration-500"
    ></div>

    <button
      @click="connectSpotify"
      :disabled="isConnected"
      class="relative flex items-center justify-between w-full bg-black border border-gray-800 text-gray-200 px-6 py-4 rounded-xl shadow-2xl transition-all overflow-hidden"
      :class="{ 'border-green-500/50': isConnected }"
    >
      <div class="flex items-center gap-4 z-10">
        <svg viewBox="0 0 24 24" aria-hidden="true" class="w-6 h-6">
          <path
            fill="#1DB954"
            d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"
          />
        </svg>

        <div class="flex flex-col text-left">
          <span
            class="font-bold text-sm tracking-wide uppercase"
            :class="{ 'text-green-400': isConnected }"
          >
            {{ buttonText }}
          </span>
          <span v-if="!isConnected" class="text-xs text-gray-500 font-mono mt-0.5">
            Upload your sonic blueprint.
          </span>
          <span v-else class="text-xs text-green-500/70 font-mono mt-0.5">
            Audio fingerprint locked.
          </span>
        </div>
      </div>

      <svg
        v-if="isConnected"
        class="z-10 w-5 h-5 text-green-500"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M5 13l4 4L19 7"
        ></path>
      </svg>
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useVibeStore } from '@/composables/useVibeStore'

const { oauthState, connectSpotify } = useVibeStore()

const isConnected = computed(() => oauthState.value.spotify.connected)

const buttonText = computed(() => {
  if (isConnected.value) return 'SPOTIFY SYNCED'
  return 'CONNECT SPOTIFY'
})
</script>
