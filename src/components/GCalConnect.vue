<template>
  <div class="relative group w-full">
    <div
      class="absolute -inset-0.5 bg-gradient-to-r from-red-600/40 to-yellow-500/40 rounded-xl blur opacity-30 group-hover:opacity-70 transition duration-500"
    ></div>

    <button
      @click="initiateGoogleAuth"
      :disabled="isConnecting || isConnected"
      class="relative flex items-center justify-between w-full bg-black border border-gray-800 text-gray-200 px-6 py-4 rounded-xl shadow-2xl transition-all overflow-hidden"
      :class="{ 'opacity-50 cursor-not-allowed': isConnecting, 'border-red-500/50': isConnected }"
    >
      <div class="flex items-center gap-4 z-10">
        <svg viewBox="0 0 24 24" aria-hidden="true" class="w-6 h-6">
          <path
            fill="#4285F4"
            d="M21.6 12.23c0-.82-.07-1.61-.2-2.37H12v4.48h5.38c-.23 1.15-.86 2.12-1.73 2.76v2.3h2.8c1.64-1.51 2.58-3.74 2.58-6.17z"
          />
          <path
            fill="#34A853"
            d="M12 22c2.7 0 4.96-.9 6.62-2.42l-2.8-2.3c-.9.6-2.06.95-3.82.95-2.93 0-5.4-1.98-6.28-4.65H2.8v2.37C4.46 19.22 7.96 22 12 22z"
          />
          <path
            fill="#FBBC05"
            d="M5.72 13.58c-.23-.68-.36-1.4-.36-2.14s.13-1.46.36-2.14V6.93H2.8C2.26 8 2 9.17 2 10.42c0 1.25.26 2.42.8 3.5l2.92-2.34z"
          />
          <path
            fill="#EA4335"
            d="M12 5.05c1.47 0 2.78.5 3.82 1.49l2.86-2.86C16.96 2.04 14.7 1 12 1 7.96 1 4.46 3.78 2.8 6.93l2.92 2.34c.88-2.67 3.35-4.65 6.28-4.65z"
          />
        </svg>

        <div class="flex flex-col text-left">
          <span
            class="font-bold text-sm tracking-wide uppercase"
            :class="{ 'text-red-400': isConnected }"
          >
            {{ buttonText }}
          </span>
          <span v-if="!isConnected" class="text-xs text-gray-500 font-mono mt-0.5">
            Sync for logistics & recovery.
          </span>
          <span v-else class="text-xs text-red-500/70 font-mono mt-0.5">
            Temporal grid locked.
          </span>
        </div>
      </div>

      <div
        v-if="isConnecting"
        class="z-10 animate-spin w-5 h-5 border-2 border-gray-500 border-t-white rounded-full"
      ></div>

      <svg
        v-if="isConnected"
        class="z-10 w-5 h-5 text-red-500"
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
const { token } = useAuthStore()
const { oauthState, markConnected } = useVibeStore()

const API = import.meta.env.VITE_API_URL || ''
const isConnecting = ref(false)

const isConnected = computed(() => oauthState.value.google.connected)

const buttonText = computed(() => {
  if (isConnecting.value) return 'AUTHORIZING PLANNER...'
  if (isConnected.value) return 'CALENDAR SYNCED'
  return 'CONNECT GOOGLE'
})

async function initiateGoogleAuth() {
  if (isConnected.value || !token.value) return
  isConnecting.value = true

  try {
    const response = await fetch(`${API}/api/auth/google/init?token=${token.value}`)
    const data = await response.json()

    if (data.auth_url) {
      window.location.href = data.auth_url
    } else {
      throw new Error('Google OAuth failed to initialize')
    }
  } catch (error) {
    console.error('Temporal sync failed:', error)
    isConnecting.value = false
  }
}

onMounted(() => {
  const { code, state, scope } = route.query

  if (code && state && !isConnected.value) {
    isConnecting.value = true

    fetch(`${API}/api/auth/google/callback?code=${code}&state=${state}`, {
      headers: { Authorization: `Bearer ${token.value}` },
    })
      .then((res) => {
        if (!res.ok) throw new Error('Google OAuth callback failed')
        markConnected('google')
        router.replace({ path: '/calibrate' })
      })
      .catch((err) => console.error('Failed to ingest Calendar data:', err))
      .finally(() => { isConnecting.value = false })
  }
})
</script>
