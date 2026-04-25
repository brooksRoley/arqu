<template>
  <div class="relative group w-full">
    <div
      class="absolute -inset-0.5 bg-gradient-to-r from-gray-800/40 to-slate-600/40 rounded-xl blur opacity-30 group-hover:opacity-70 transition duration-500"
    ></div>

    <button
      @click="initiateGitHubAuth"
      :disabled="isConnecting || isConnected"
      class="relative flex items-center justify-between w-full bg-black border border-gray-800 text-gray-200 px-6 py-4 rounded-xl shadow-2xl transition-all overflow-hidden"
      :class="{ 'opacity-50 cursor-not-allowed': isConnecting, 'border-[#f0f6fc]/50': isConnected }"
    >
      <div class="flex items-center gap-4 z-10">
        <svg viewBox="0 0 24 24" aria-hidden="true" class="w-6 h-6 fill-current text-[#f0f6fc]">
          <path d="M12 0C5.374 0 0 5.373 0 12c0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0 1 12 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z" />
        </svg>

        <div class="flex flex-col text-left">
          <span
            class="font-bold text-sm tracking-wide uppercase"
            :class="{ 'text-[#f0f6fc]': isConnected }"
          >
            {{ buttonText }}
          </span>
          <span v-if="!isConnected" class="text-xs text-gray-500 font-mono mt-0.5">
            Map your maker instinct.
          </span>
          <span v-else class="text-xs text-[#f0f6fc]/70 font-mono mt-0.5">
            Code graph locked.
          </span>
        </div>
      </div>

      <div
        v-if="isConnecting"
        class="z-10 animate-spin w-5 h-5 border-2 border-gray-500 border-t-white rounded-full"
      ></div>

      <svg
        v-if="isConnected"
        class="z-10 w-5 h-5 text-[#f0f6fc]"
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

const isConnected = computed(() => oauthState.value.github.connected)

const buttonText = computed(() => {
  if (isConnecting.value) return 'SCANNING REPOS...'
  if (isConnected.value) return 'GITHUB SYNCED'
  return 'CONNECT GITHUB'
})

async function initiateGitHubAuth() {
  if (isConnected.value || !token.value) return
  isConnecting.value = true

  try {
    const response = await fetch(`${API}/api/github/connect?token=${token.value}`)
    if (response.status === 401) {
      logout()
      window.location.href = '/login'
      return
    }
    const data = await response.json()

    if (data.auth_url) {
      window.location.href = data.auth_url
    } else {
      throw new Error('GitHub OAuth failed to initialize')
    }
  } catch (error) {
    console.error('Code graph failed:', error)
    isConnecting.value = false
  }
}

onMounted(() => {
  // GitHub callback redirects back with ?github=connected
  if (route.query.github === 'connected' && !isConnected.value) {
    markConnected('github')
    router.replace({ path: '/calibrate' })
  }
})
</script>
