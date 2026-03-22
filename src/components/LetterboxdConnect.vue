<template>
  <div class="relative group w-full">
    <div
      class="absolute -inset-0.5 bg-gradient-to-r from-emerald-600/40 to-teal-500/40 rounded-xl blur opacity-30 group-hover:opacity-70 transition duration-500"
    ></div>

    <button
      @click="initiateLetterboxdAuth"
      :disabled="isConnecting || isConnected"
      class="relative flex items-center justify-between w-full bg-black border border-gray-800 text-gray-200 px-6 py-4 rounded-xl shadow-2xl transition-all overflow-hidden"
      :class="{ 'opacity-50 cursor-not-allowed': isConnecting, 'border-emerald-500/50': isConnected }"
    >
      <div class="flex items-center gap-4 z-10">
        <svg viewBox="0 0 24 24" aria-hidden="true" class="w-6 h-6">
          <circle cx="8" cy="12" r="5" fill="#00E054" opacity="0.85" />
          <circle cx="16" cy="12" r="5" fill="#40BCF4" opacity="0.85" />
          <path
            d="M12 8.8a5 5 0 0 1 0 6.4 5 5 0 0 1 0-6.4z"
            fill="#fff"
            opacity="0.9"
          />
        </svg>

        <div class="flex flex-col text-left">
          <span
            class="font-bold text-sm tracking-wide uppercase"
            :class="{ 'text-emerald-400': isConnected }"
          >
            {{ buttonText }}
          </span>
          <span v-if="!isConnected" class="text-xs text-gray-500 font-mono mt-0.5">
            Surrender your empathy simulator.
          </span>
          <span v-else class="text-xs text-emerald-500/70 font-mono mt-0.5">
            Diary absorbed.
          </span>
        </div>
      </div>

      <div
        v-if="isConnecting"
        class="z-10 animate-spin w-5 h-5 border-2 border-gray-500 border-t-white rounded-full"
      ></div>

      <svg
        v-if="isConnected"
        class="z-10 w-5 h-5 text-emerald-500"
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

const isConnected = computed(() => oauthState.value.letterboxd.connected)

const buttonText = computed(() => {
  if (isConnecting.value) return 'SCANNING DIARY...'
  if (isConnected.value) return 'LETTERBOXD SYNCED'
  return 'CONNECT LETTERBOXD'
})

async function initiateLetterboxdAuth() {
  if (isConnected.value || !token.value) return
  isConnecting.value = true

  try {
    const response = await fetch(`${API}/api/auth/letterboxd/init?token=${token.value}`)
    const data = await response.json()

    if (data.auth_url) {
      window.location.href = data.auth_url
    } else {
      throw new Error('Letterboxd OAuth failed to initialize')
    }
  } catch (error) {
    console.error('Empathy simulator offline:', error)
    isConnecting.value = false
  }
}

onMounted(() => {
  const { code, state } = route.query

  if (code && state && route.query.provider === 'letterboxd' && !isConnected.value) {
    isConnecting.value = true

    fetch(`${API}/api/auth/letterboxd/callback?code=${code}&state=${state}`, {
      headers: { Authorization: `Bearer ${token.value}` },
    })
      .then((res) => {
        if (!res.ok) throw new Error('Letterboxd OAuth callback failed')
        markConnected('letterboxd')
        router.replace({ path: '/peripheral' })
      })
      .catch((err) => console.error('Failed to ingest Letterboxd data:', err))
      .finally(() => { isConnecting.value = false })
  }
})
</script>
