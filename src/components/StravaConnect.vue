<template>
  <div class="relative group w-full">
    <div
      class="absolute -inset-0.5 bg-gradient-to-r from-orange-600/40 to-red-500/40 rounded-xl blur opacity-30 group-hover:opacity-70 transition duration-500"
    ></div>

    <button
      @click="initiateStravaAuth"
      :disabled="isConnecting || isConnected"
      class="relative flex items-center justify-between w-full bg-black border border-gray-800 text-gray-200 px-6 py-4 rounded-xl shadow-2xl transition-all overflow-hidden"
      :class="{ 'opacity-50 cursor-not-allowed': isConnecting, 'border-orange-500/50': isConnected }"
    >
      <div class="flex items-center gap-4 z-10">
        <svg viewBox="0 0 24 24" aria-hidden="true" class="w-6 h-6 fill-current text-[#FC4C02]">
          <path d="M15.387 17.944l-2.089-4.116h-3.065L15.387 24l5.15-10.172h-3.066m-7.008-5.599l2.836 5.598h4.172L10.463 0l-7 13.828h4.169" />
        </svg>

        <div class="flex flex-col text-left">
          <span
            class="font-bold text-sm tracking-wide uppercase"
            :class="{ 'text-orange-400': isConnected }"
          >
            {{ buttonText }}
          </span>
          <span v-if="!isConnected" class="text-xs text-gray-500 font-mono mt-0.5">
            Sync your somatic ledger.
          </span>
          <span v-else class="text-xs text-orange-500/70 font-mono mt-0.5">
            Exertion mapped.
          </span>
        </div>
      </div>

      <div
        v-if="isConnecting"
        class="z-10 animate-spin w-5 h-5 border-2 border-gray-500 border-t-white rounded-full"
      ></div>

      <svg
        v-if="isConnected"
        class="z-10 w-5 h-5 text-orange-500"
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
import { ref, computed } from 'vue'
import { useAuthStore } from '@/composables/useAuthStore'
import { useVibeStore } from '@/composables/useVibeStore'

const { token } = useAuthStore()
const { oauthState } = useVibeStore()

const API = import.meta.env.VITE_API_URL || ''
const isConnecting = ref(false)

const isConnected = computed(() => oauthState.value.strava.connected)

const buttonText = computed(() => {
  if (isConnecting.value) return 'MAPPING EXERTION...'
  if (isConnected.value) return 'STRAVA SYNCED'
  return 'CONNECT STRAVA'
})

async function initiateStravaAuth() {
  if (isConnected.value || !token.value) return
  isConnecting.value = true

  try {
    const response = await fetch(`${API}/api/strava/connect?token=${token.value}`)
    const data = await response.json()

    if (data.auth_url) {
      window.location.href = data.auth_url
    } else {
      throw new Error('Strava OAuth failed to initialize')
    }
  } catch (error) {
    console.error('Somatic sync failed:', error)
    isConnecting.value = false
  }
}
</script>
