<template>
  <div class="relative group w-full">
    <div
      class="absolute -inset-0.5 bg-gradient-to-r from-blue-900/40 to-slate-700/40 rounded-xl blur opacity-30 group-hover:opacity-70 transition duration-500"
    ></div>

    <button
      @click="initiateSteamAuth"
      :disabled="isConnecting || isConnected"
      class="relative flex items-center justify-between w-full bg-black border border-gray-800 text-gray-200 px-6 py-4 rounded-xl shadow-2xl transition-all overflow-hidden"
      :class="{ 'opacity-50 cursor-not-allowed': isConnecting, 'border-blue-500/50': isConnected }"
    >
      <div class="flex items-center gap-4 z-10">
        <svg viewBox="0 0 24 24" aria-hidden="true" class="w-6 h-6 fill-current text-[#c7d5e0]">
          <path d="M11.979 0C5.678 0 .511 4.86.022 10.96l6.432 2.658a3.387 3.387 0 0 1 1.912-.587c.063 0 .125.003.187.006l2.861-4.142V8.86c0-2.491 2.026-4.518 4.518-4.518 2.494 0 4.52 2.027 4.52 4.518 0 2.494-2.026 4.52-4.52 4.52h-.105l-4.076 2.91c0 .05.004.1.004.15 0 1.87-1.52 3.39-3.39 3.39a3.394 3.394 0 0 1-3.349-2.858L.453 15.17A11.98 11.98 0 0 0 11.979 24c6.627 0 12-5.373 12-12s-5.373-12-12-12zM7.54 18.21l-1.473-.61a2.539 2.539 0 0 0 4.86-.925 2.545 2.545 0 0 0-2.542-2.54c-.18 0-.357.02-.53.055l1.523.63a1.868 1.868 0 1 1-1.838 3.39zm8.392-4.882a3.012 3.012 0 0 1-3.01-3.012 3.01 3.01 0 0 1 3.01-3.01 3.013 3.013 0 0 1 3.012 3.01 3.014 3.014 0 0 1-3.012 3.012zm-.002-5.27a2.262 2.262 0 0 0-2.26 2.258 2.261 2.261 0 1 0 2.26-2.258z" />
        </svg>

        <div class="flex flex-col text-left">
          <span
            class="font-bold text-sm tracking-wide uppercase"
            :class="{ 'text-blue-400': isConnected }"
          >
            {{ buttonText }}
          </span>
          <span v-if="!isConnected" class="text-xs text-gray-500 font-mono mt-0.5">
            Quantify your isolation hours.
          </span>
          <span v-else class="text-xs text-blue-500/70 font-mono mt-0.5">
            Isolation metric locked.
          </span>
        </div>
      </div>

      <div
        v-if="isConnecting"
        class="z-10 animate-spin w-5 h-5 border-2 border-gray-500 border-t-white rounded-full"
      ></div>

      <svg
        v-if="isConnected"
        class="z-10 w-5 h-5 text-blue-500"
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
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/composables/useAuthStore'
import { useVibeStore } from '@/composables/useVibeStore'

const route = useRoute()
const router = useRouter()
const { token, logout } = useAuthStore()
const { oauthState, markConnected } = useVibeStore()

const API = import.meta.env.VITE_API_URL || ''
const isConnecting = ref(false)

const isConnected = computed(() => oauthState.value.steam.connected)

const buttonText = computed(() => {
  if (isConnecting.value) return 'VERIFYING IDENTITY...'
  if (isConnected.value) return 'STEAM SYNCED'
  return 'CONNECT STEAM'
})

async function initiateSteamAuth() {
  if (isConnected.value || !token.value) return
  isConnecting.value = true

  try {
    const response = await fetch(`${API}/api/steam/connect?token=${token.value}`)
    if (response.status === 401) {
      logout()
      window.location.href = '/login'
      return
    }
    const data = await response.json()

    if (data.auth_url) {
      window.location.href = data.auth_url
    } else {
      throw new Error('Steam OpenID failed to initialize')
    }
  } catch (error) {
    console.error('Isolation metric failed:', error)
    isConnecting.value = false
  }
}

onMounted(() => {
  // Steam callback redirects back with ?steam=connected
  if (route.query.steam === 'connected' && !isConnected.value) {
    markConnected('steam')
    router.replace({ path: '/calibrate' })
  }
})
</script>
