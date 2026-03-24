<template>
  <div class="min-h-screen bg-gray-900 flex items-center justify-center">
    <div class="text-center space-y-4">
      <div v-if="!errorMsg" class="animate-spin w-8 h-8 border-2 border-gray-500 border-t-red-400 rounded-full mx-auto"></div>
      <p class="text-gray-400 text-sm font-mono">
        {{ errorMsg || 'Syncing temporal grid...' }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/composables/useAuthStore'

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

  try {
    await loginWithProvider('google', code)
    router.replace('/calibrate')
  } catch (e: any) {
    errorMsg.value = e.message || 'Google sign-in failed.'
  }
})
</script>
