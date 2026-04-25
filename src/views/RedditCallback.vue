<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useVibeStore } from '@/composables/useVibeStore'

const route = useRoute()
const router = useRouter()
const { markConnected } = useVibeStore()
const API = import.meta.env.VITE_API_URL || ''

onMounted(async () => {
  const code = route.query.code as string
  const state = route.query.state as string
  if (!code || !state) { router.replace('/calibrate'); return }
  try {
    const res = await fetch(`${API}/api/reddit/callback?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}`)
    if (res.ok) markConnected('reddit')
  } catch { /* ignore */ }
  router.replace('/calibrate')
})
</script>
<template><div class="min-h-screen bg-black flex items-center justify-center"><div class="animate-spin w-8 h-8 border-2 border-gray-700 border-t-white rounded-full" /></div></template>
