<template>
  <div class="relative group w-full">
    <div
      class="absolute -inset-0.5 bg-gradient-to-r from-indigo-600/40 to-purple-900/40 rounded-xl blur opacity-30 group-hover:opacity-70 transition duration-500"
    ></div>

    <button
      @click="showModal = true"
      :disabled="isConnecting || isConnected"
      class="relative flex items-center justify-between w-full bg-black border border-gray-800 text-gray-200 px-6 py-4 rounded-xl shadow-2xl transition-all overflow-hidden"
      :class="{ 'opacity-50 cursor-not-allowed': isConnecting, 'border-indigo-500/50': isConnected }"
    >
      <div class="flex items-center gap-4 z-10">
        <svg viewBox="0 0 24 24" aria-hidden="true" class="w-6 h-6">
          <circle cx="12" cy="12" r="3" fill="#a78bfa" />
          <circle cx="12" cy="12" r="7" stroke="#a78bfa" stroke-width="0.75" fill="none" opacity="0.6" />
          <circle cx="12" cy="12" r="11" stroke="#a78bfa" stroke-width="0.5" fill="none" opacity="0.3" />
          <line x1="12" y1="1" x2="12" y2="4" stroke="#a78bfa" stroke-width="0.75" opacity="0.5" />
          <line x1="12" y1="20" x2="12" y2="23" stroke="#a78bfa" stroke-width="0.75" opacity="0.5" />
          <line x1="1" y1="12" x2="4" y2="12" stroke="#a78bfa" stroke-width="0.75" opacity="0.5" />
          <line x1="20" y1="12" x2="23" y2="12" stroke="#a78bfa" stroke-width="0.75" opacity="0.5" />
        </svg>

        <div class="flex flex-col text-left">
          <span
            class="font-bold text-sm tracking-wide uppercase"
            :class="{ 'text-indigo-400': isConnected }"
          >
            {{ buttonText }}
          </span>
          <span v-if="!isConnected" class="text-xs text-gray-500 font-mono mt-0.5">
            Let us read your constellations.
          </span>
          <span v-else class="text-xs text-indigo-500/70 font-mono mt-0.5">
            Chart ingested.
          </span>
        </div>
      </div>

      <div
        v-if="isConnecting"
        class="z-10 animate-spin w-5 h-5 border-2 border-gray-500 border-t-white rounded-full"
      ></div>

      <svg
        v-if="isConnected"
        class="z-10 w-5 h-5 text-indigo-500"
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

    <!-- Credential modal (Co-Star has no public API) -->
    <Teleport to="body">
      <div
        v-if="showModal"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
        @click.self="showModal = false"
      >
        <div class="bg-gray-900 border border-indigo-500/30 rounded-2xl p-8 w-full max-w-md shadow-2xl space-y-6">
          <div class="text-center space-y-2">
            <h3 class="text-xl font-bold text-indigo-400">Co&#8239;&#8212;&#8239;Star Proxy Sync</h3>
            <p class="text-xs text-gray-500 font-mono">
              Credentials are transmitted once and immediately purged. We never store your password.
            </p>
          </div>

          <form @submit.prevent="submitCoStar" class="space-y-4">
            <input
              v-model="costarUsername"
              type="text"
              placeholder="Co-Star username or email"
              autocomplete="username"
              class="w-full bg-black border border-gray-700 rounded-lg px-4 py-3 text-gray-200 placeholder-gray-600 focus:border-indigo-500 focus:outline-none font-mono text-sm"
            />
            <input
              v-model="costarPassword"
              type="password"
              placeholder="Co-Star password"
              autocomplete="current-password"
              class="w-full bg-black border border-gray-700 rounded-lg px-4 py-3 text-gray-200 placeholder-gray-600 focus:border-indigo-500 focus:outline-none font-mono text-sm"
            />
            <div class="flex gap-3">
              <button
                type="button"
                @click="showModal = false"
                class="flex-1 py-3 rounded-lg border border-gray-700 text-gray-400 hover:border-gray-500 transition-colors font-mono text-sm"
              >
                ABORT
              </button>
              <button
                type="submit"
                :disabled="!costarUsername || !costarPassword || isConnecting"
                class="flex-1 py-3 rounded-lg bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed text-white font-bold transition-colors font-mono text-sm"
              >
                {{ isConnecting ? 'INGESTING...' : 'SYNC CHART' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAuthStore } from '@/composables/useAuthStore'
import { useVibeStore } from '@/composables/useVibeStore'

const { token } = useAuthStore()
const { oauthState, markConnected } = useVibeStore()

const API = import.meta.env.VITE_API_URL || ''
const isConnecting = ref(false)
const showModal = ref(false)
const costarUsername = ref('')
const costarPassword = ref('')

const isConnected = computed(() => oauthState.value.costar.connected)

const buttonText = computed(() => {
  if (isConnecting.value) return 'READING THE VOID...'
  if (isConnected.value) return 'CHART SYNCED'
  return 'CONNECT CO—STAR'
})

async function submitCoStar() {
  if (isConnected.value || !token.value) return
  isConnecting.value = true

  try {
    const res = await fetch(`${API}/api/auth/costar/ingest`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token.value}`,
      },
      body: JSON.stringify({
        costar_username: costarUsername.value,
        costar_password: costarPassword.value,
      }),
    })

    if (!res.ok) throw new Error('Co-Star ingestion failed')
    markConnected('costar')
    showModal.value = false
  } catch (error) {
    console.error('Fatalistic mirror shattered:', error)
  } finally {
    // Purge credentials from memory immediately
    costarPassword.value = ''
    costarUsername.value = ''
    isConnecting.value = false
  }
}
</script>
