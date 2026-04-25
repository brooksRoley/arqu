<template>
  <div class="relative group w-full">
    <div
      class="absolute -inset-0.5 bg-gradient-to-r from-orange-900/40 to-red-700/40 rounded-xl blur opacity-30 group-hover:opacity-70 transition duration-500"
    ></div>

    <button
      @click="initiateRedditAuth"
      :disabled="isConnecting || isConnected"
      class="relative flex items-center justify-between w-full bg-black border border-gray-800 text-gray-200 px-6 py-4 rounded-xl shadow-2xl transition-all overflow-hidden"
      :class="{ 'opacity-50 cursor-not-allowed': isConnecting, 'border-[#FF4500]/50': isConnected }"
    >
      <div class="flex items-center gap-4 z-10">
        <svg viewBox="0 0 24 24" aria-hidden="true" class="w-6 h-6 fill-current text-[#FF4500]">
          <path d="M12 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0zm5.01 4.744c.688 0 1.25.561 1.25 1.249a1.25 1.25 0 0 1-2.498.056l-2.597-.547-.8 3.747c1.824.07 3.48.632 4.674 1.488.308-.309.73-.491 1.207-.491.968 0 1.754.786 1.754 1.754 0 .716-.435 1.333-1.01 1.614a3.111 3.111 0 0 1 .042.52c0 2.694-3.13 4.87-7.004 4.87-3.874 0-7.004-2.176-7.004-4.87 0-.183.015-.366.043-.534A1.748 1.748 0 0 1 4.028 12c0-.968.786-1.754 1.754-1.754.463 0 .898.196 1.207.49 1.207-.883 2.878-1.43 4.744-1.487l.885-4.182a.342.342 0 0 1 .14-.197.35.35 0 0 1 .238-.042l2.906.617a1.214 1.214 0 0 1 1.108-.701zM9.25 12C8.561 12 8 12.562 8 13.25c0 .687.561 1.248 1.25 1.248.687 0 1.248-.561 1.248-1.249 0-.688-.561-1.249-1.249-1.249zm5.5 0c-.687 0-1.248.561-1.248 1.25 0 .687.561 1.248 1.249 1.248.688 0 1.249-.561 1.249-1.249 0-.687-.562-1.249-1.25-1.249zm-5.466 3.99a.327.327 0 0 0-.231.094.33.33 0 0 0 0 .463c.842.842 2.484.913 2.961.913.477 0 2.105-.056 2.961-.913a.361.361 0 0 0 0-.463.327.327 0 0 0-.462 0c-.547.533-1.684.73-2.512.73-.828 0-1.979-.196-2.512-.73a.326.326 0 0 0-.205-.094z" />
        </svg>

        <div class="flex flex-col text-left">
          <span
            class="font-bold text-sm tracking-wide uppercase"
            :class="{ 'text-[#FF4500]': isConnected }"
          >
            {{ buttonText }}
          </span>
          <span v-if="!isConnected" class="text-xs text-gray-500 font-mono mt-0.5">
            Surface your anonymous self.
          </span>
          <span v-else class="text-xs text-[#FF4500]/70 font-mono mt-0.5">
            Psyche mapped.
          </span>
        </div>
      </div>

      <div
        v-if="isConnecting"
        class="z-10 animate-spin w-5 h-5 border-2 border-gray-500 border-t-white rounded-full"
      ></div>

      <svg
        v-if="isConnected"
        class="z-10 w-5 h-5 text-[#FF4500]"
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

const isConnected = computed(() => oauthState.value.reddit.connected)

const buttonText = computed(() => {
  if (isConnecting.value) return 'MINING SUBREDDITS...'
  if (isConnected.value) return 'REDDIT SYNCED'
  return 'CONNECT REDDIT'
})

async function initiateRedditAuth() {
  if (isConnected.value || !token.value) return
  isConnecting.value = true

  try {
    const response = await fetch(`${API}/api/reddit/connect?token=${token.value}`)
    if (response.status === 401) {
      logout()
      window.location.href = '/login'
      return
    }
    const data = await response.json()

    if (data.auth_url) {
      window.location.href = data.auth_url
    } else {
      throw new Error('Reddit OAuth failed to initialize')
    }
  } catch (error) {
    console.error('Psyche mapping failed:', error)
    isConnecting.value = false
  }
}

onMounted(() => {
  // Reddit callback redirects back with ?reddit=connected
  if (route.query.reddit === 'connected' && !isConnected.value) {
    markConnected('reddit')
    router.replace({ path: '/calibrate' })
  }
})
</script>
