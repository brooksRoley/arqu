<template>
  <div class="relative group w-full">
    <div
      class="absolute -inset-0.5 bg-gradient-to-r from-gray-700 to-gray-900 rounded-xl blur opacity-30 group-hover:opacity-70 transition duration-500"
    ></div>

    <button
      @click="initiateXAuth"
      :disabled="isConnecting || isConnected"
      class="relative flex items-center justify-between w-full bg-black border border-gray-800 text-gray-200 px-6 py-4 rounded-xl shadow-2xl transition-all overflow-hidden"
      :class="{ 'opacity-50 cursor-not-allowed': isConnecting, 'border-green-500/50': isConnected }"
    >
      <div class="flex items-center gap-4 z-10">
        <svg viewBox="0 0 24 24" aria-hidden="true" class="w-6 h-6 fill-current text-white">
          <path
            d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 22.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"
          ></path>
        </svg>

        <div class="flex flex-col text-left">
          <span
            class="font-bold text-sm tracking-wide uppercase"
            :class="{ 'text-green-400': isConnected }"
          >
            {{ buttonText }}
          </span>
          <span v-if="!isConnected" class="text-xs text-gray-500 font-mono mt-0.5">
            Inject your neurotic footprint.
          </span>
          <span v-else class="text-xs text-green-500/70 font-mono mt-0.5">Vector armed.</span>
        </div>
      </div>

      <div
        v-if="isConnecting"
        class="z-10 animate-spin w-5 h-5 border-2 border-gray-500 border-t-white rounded-full"
      ></div>

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
import { ref, computed } from 'vue'
import { useAuthStore } from '@/composables/useAuthStore'
import { useVibeStore } from '@/composables/useVibeStore'

const { token } = useAuthStore()
const { oauthState } = useVibeStore()

const X_CLIENT_ID = import.meta.env.VITE_X_CLIENT_ID || ''
const X_REDIRECT_URI = import.meta.env.VITE_X_REDIRECT_URI || `${window.location.origin}/auth/x/callback`
const VERIFIER_KEY = 'channelzero-x-pkce-verifier'

const isConnecting = ref(false)
const isConnected = computed(() => oauthState.value.twitter.connected)

const buttonText = computed(() => {
  if (isConnecting.value) return 'ESTABLISHING HANDSHAKE...'
  if (isConnected.value) return 'X VECTOR SYNCED'
  return 'CONNECT X (TWITTER)'
})

// ── PKCE helpers ──────────────────────────────────────────────
function generateVerifier(): string {
  const array = new Uint8Array(32)
  crypto.getRandomValues(array)
  return Array.from(array, (b) => b.toString(16).padStart(2, '0')).join('')
}

async function sha256(plain: string): Promise<ArrayBuffer> {
  const encoder = new TextEncoder()
  return crypto.subtle.digest('SHA-256', encoder.encode(plain))
}

function base64url(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer)
  let binary = ''
  bytes.forEach((b) => (binary += String.fromCharCode(b)))
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')
}

async function initiateXAuth() {
  if (isConnected.value || !token.value) return
  isConnecting.value = true

  const codeVerifier = generateVerifier()
  const codeChallenge = base64url(await sha256(codeVerifier))

  // Store verifier so the callback page can retrieve it
  localStorage.setItem(VERIFIER_KEY, codeVerifier)

  const params = new URLSearchParams({
    response_type: 'code',
    client_id: X_CLIENT_ID,
    redirect_uri: X_REDIRECT_URI,
    scope: 'tweet.read users.read offline.access',
    state: 'x-oauth',
    code_challenge: codeChallenge,
    code_challenge_method: 'S256',
  })

  window.location.href = `https://twitter.com/i/oauth2/authorize?${params}`
}
</script>
