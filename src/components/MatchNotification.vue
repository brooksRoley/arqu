<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/composables/useAuthStore'

interface NewMatch {
  user_id: string
  display_name: string
  avatar_url: string | null
  matched_at: string
}

const router = useRouter()
const { apiFetch, isAuthenticated } = useAuthStore()
const matches = ref<NewMatch[]>([])
const visible = ref(false)

let checkTimer: ReturnType<typeof setInterval> | null = null
let dismissTimer: ReturnType<typeof setTimeout> | null = null

async function checkNewMatches() {
  if (!isAuthenticated.value) return
  try {
    const data = await apiFetch<NewMatch[]>('/api/match/new')
    if (data.length > 0) {
      matches.value = data
      visible.value = true
      // Auto-dismiss after 12 seconds
      if (dismissTimer) clearTimeout(dismissTimer)
      dismissTimer = setTimeout(() => { visible.value = false }, 12000)
    }
  } catch { /* silent */ }
}

async function goToMessages() {
  // Mark as seen
  try {
    await apiFetch('/api/match/seen', { method: 'POST' })
  } catch { /* silent */ }
  visible.value = false
  matches.value = []
  router.push('/messages')
}

function dismiss() {
  visible.value = false
}

onMounted(() => {
  checkNewMatches()
  checkTimer = setInterval(checkNewMatches, 30000)
})

onUnmounted(() => {
  if (checkTimer) clearInterval(checkTimer)
  if (dismissTimer) clearTimeout(dismissTimer)
})
</script>

<template>
  <Transition name="toast">
    <div
      v-if="visible && matches.length > 0"
      class="fixed top-4 right-4 z-50 max-w-sm"
    >
      <div
        class="bg-gray-900 border border-purple-500/40 rounded-xl p-4 shadow-lg shadow-purple-500/10 cursor-pointer"
        @click="goToMessages"
      >
        <div class="flex items-center justify-between mb-2">
          <span class="text-xs font-semibold uppercase tracking-wider text-purple-400">New Match</span>
          <button
            @click.stop="dismiss"
            class="text-gray-600 hover:text-gray-400 text-sm leading-none"
          >&times;</button>
        </div>
        <div v-for="m in matches.slice(0, 3)" :key="m.user_id" class="flex items-center gap-3 mt-2">
          <div class="w-8 h-8 rounded-full bg-purple-900/50 flex items-center justify-center text-purple-300 text-xs font-bold shrink-0">
            {{ m.display_name.charAt(0).toUpperCase() }}
          </div>
          <div>
            <div class="text-sm text-white font-medium">{{ m.display_name }}</div>
            <div class="text-xs text-gray-500">Tap to message</div>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.toast-enter-active { transition: all 0.3s ease-out; }
.toast-leave-active { transition: all 0.2s ease-in; }
.toast-enter-from { opacity: 0; transform: translateY(-12px) scale(0.95); }
.toast-leave-to { opacity: 0; transform: translateY(-8px) scale(0.98); }
</style>
