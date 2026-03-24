<template>
  <div class="min-h-screen bg-gray-900 flex items-center justify-center">
    <div class="text-center space-y-4">
      <div v-if="!errorMsg" class="animate-spin w-8 h-8 border-2 border-gray-500 border-t-blue-400 rounded-full mx-auto"></div>
      <p class="text-gray-400 text-sm font-mono">
        {{ errorMsg || 'Decoding neurotic imprint...' }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/composables/useAuthStore'

const VERIFIER_KEY = 'channelzero-x-pkce-verifier'

const route = useRoute()
const router = useRouter()
const { loginWithProvider } = useAuthStore()
const errorMsg = ref<string | null>(null)

onMounted(async () => {
  const code = route.query.code as string | undefined
  if (!code) {
    errorMsg.value = 'Missing authorization code.'
    return
  }

  const codeVerifier = localStorage.getItem(VERIFIER_KEY)
  if (!codeVerifier) {
    errorMsg.value = 'Missing PKCE verifier — please retry the connection.'
    return
  }

  try {
    await loginWithProvider('x', code, codeVerifier)
    localStorage.removeItem(VERIFIER_KEY)
    router.replace('/calibrate')
  } catch (e: any) {
    errorMsg.value = e.message || 'X sign-in failed.'
  }
})
</script>
