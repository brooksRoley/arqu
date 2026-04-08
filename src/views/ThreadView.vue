<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/composables/useAuthStore'
import { useMessageStore } from '@/composables/useMessageStore'
import { useVibeStore } from '@/composables/useVibeStore'

const route = useRoute()
const router = useRouter()
const { user, isAuthenticated } = useAuthStore()
const {
  activeThread, activeUserId, sending, loadingThread, error,
  openThread, sendMessage, startPolling, stopPolling, clearThread,
} = useMessageStore()

if (!isAuthenticated.value) router.replace('/login')

// Resolve match metadata (name, match reason) from vibeStore if available
const { matches } = useVibeStore()

const otherUserId = computed(() => route.params.userId as string)
const otherUserName = ref('—')

const matchMeta = computed(() =>
  matches.value.find((m) => m.user_id === otherUserId.value) ?? null
)

// ── Oracle-seeded opener ─────────────────────────────────────────────────────

const oracleOpener = computed(() => {
  const m = matchMeta.value
  if (!m) return null
  const pct = Math.round(m.similarity * 100)
  const sonic = m.sonic_overlap
  if (sonic && sonic.shared_genres.length > 0) {
    const genre = sonic.shared_genres[0]
    return `Your frequencies overlap at ${pct}%. The Oracle suggests: "What ${genre} track have you had on repeat this week?"`
  }
  return `Your vectors aligned at ${pct}%. The Oracle suggests: "What's been taking up most of your mental space lately?"`
})

const showOpener = computed(
  () => oracleOpener.value !== null && activeThread.value.length === 0 && !loadingThread.value,
)

// ── Input ─────────────────────────────────────────────────────────────────────

const inputText = ref('')
const inputEl = ref<HTMLTextAreaElement | null>(null)
const scrollEl = ref<HTMLElement | null>(null)

function scrollToBottom() {
  nextTick(() => {
    if (scrollEl.value) scrollEl.value.scrollTop = scrollEl.value.scrollHeight
  })
}

async function submit() {
  const body = inputText.value.trim()
  if (!body || sending.value) return
  inputText.value = ''
  await sendMessage(otherUserId.value, body)
  scrollToBottom()
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    submit()
  }
}

function useOpener() {
  inputText.value = oracleOpener.value?.replace(/^.*?"/, '').replace(/"$/, '') ?? ''
  inputEl.value?.focus()
}

// ── Timestamp formatting ──────────────────────────────────────────────────────

function formatTime(iso: string): string {
  const d = new Date(iso)
  const now = new Date()
  const diffDays = Math.floor((now.getTime() - d.getTime()) / 86400000)
  if (diffDays === 0) return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  if (diffDays === 1) return `Yesterday ${d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`
  return d.toLocaleDateString([], { month: 'short', day: 'numeric' })
}

// ── Lifecycle ─────────────────────────────────────────────────────────────────

watch(activeThread, scrollToBottom)

onMounted(async () => {
  await openThread(otherUserId.value)
  // Resolve display name from match data or thread list
  const m = matchMeta.value
  if (m) {
    otherUserName.value = m.display_name
  }
  startPolling(5000)
  scrollToBottom()
})

onUnmounted(() => {
  stopPolling()
  clearThread()
})
</script>

<template>
  <div class="thread">
    <!-- Header -->
    <div class="thread-header">
      <button class="back-btn" @click="router.back()">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M19 12H5M12 19l-7-7 7-7"/>
        </svg>
      </button>
      <div class="header-info">
        <span class="header-name">{{ matchMeta?.display_name ?? otherUserName }}</span>
        <span v-if="matchMeta" class="header-sub">
          {{ Math.round(matchMeta.similarity * 100) }}% vibe alignment
          <span v-if="matchMeta.attachment_style"> · {{ matchMeta.attachment_style }}</span>
        </span>
      </div>
    </div>

    <!-- Messages -->
    <div class="thread-body" ref="scrollEl">
      <div v-if="loadingThread" class="thread-loading">
        <span class="loading-dot"></span>
        <span class="loading-dot"></span>
        <span class="loading-dot"></span>
      </div>

      <div v-else-if="error" class="thread-error">{{ error }}</div>

      <!-- Oracle opener card -->
      <div v-if="showOpener" class="oracle-card">
        <span class="oracle-icon">◈</span>
        <p class="oracle-suggestion">{{ oracleOpener }}</p>
        <button class="oracle-use-btn" @click="useOpener">Use this opener</button>
      </div>

      <!-- Message bubbles -->
      <template v-for="msg in activeThread" :key="msg.id">
        <div
          class="bubble-row"
          :class="msg.sender_id === user?.id ? 'bubble-row--self' : 'bubble-row--other'"
        >
          <div class="bubble" :class="msg.sender_id === user?.id ? 'bubble--self' : 'bubble--other'">
            <span class="bubble-text">{{ msg.body }}</span>
            <span class="bubble-time">{{ formatTime(msg.created_at) }}</span>
          </div>
        </div>
      </template>

      <div v-if="activeThread.length === 0 && !loadingThread && !showOpener" class="thread-empty">
        No messages yet. Say something.
      </div>
    </div>

    <!-- Input -->
    <div class="thread-input-row">
      <textarea
        ref="inputEl"
        v-model="inputText"
        class="thread-input"
        placeholder="Write something real..."
        rows="1"
        :disabled="sending"
        @keydown="onKeydown"
      ></textarea>
      <button
        class="send-btn"
        :disabled="!inputText.trim() || sending"
        @click="submit"
      >
        <svg v-if="!sending" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M22 2L11 13M22 2L15 22l-4-9-9-4 20-7z"/>
        </svg>
        <span v-else class="send-spinner"></span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.thread {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 3rem);
  background: #08060e;
  color: #e2e8f0;
}

/* ── Header ── */
.thread-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(10, 8, 20, 0.9);
  backdrop-filter: blur(10px);
  flex-shrink: 0;
}

.back-btn {
  background: none;
  border: none;
  color: #64748b;
  cursor: pointer;
  padding: 0.25rem;
  display: flex;
  align-items: center;
  transition: color 0.15s;
}

.back-btn:hover { color: #e2e8f0; }

.back-btn svg { width: 20px; height: 20px; }

.header-info {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.header-name {
  font-size: 1rem;
  font-weight: 600;
  color: #e2e8f0;
}

.header-sub {
  font-size: 0.72rem;
  color: #6366f1;
}

/* ── Body ── */
.thread-body {
  flex: 1;
  overflow-y: auto;
  padding: 1.25rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  scrollbar-width: thin;
  scrollbar-color: rgba(99, 102, 241, 0.2) transparent;
}

/* Loading dots */
.thread-loading {
  display: flex;
  gap: 0.4rem;
  justify-content: center;
  padding: 2rem;
}

.loading-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #6366f1;
  animation: dot-pulse 1.2s ease-in-out infinite;
}

.loading-dot:nth-child(2) { animation-delay: 0.2s; }
.loading-dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes dot-pulse {
  0%, 80%, 100% { opacity: 0.2; transform: scale(0.8); }
  40%            { opacity: 1;   transform: scale(1);   }
}

.thread-error {
  text-align: center;
  color: #ef4444;
  font-size: 0.85rem;
  padding: 2rem;
}

.thread-empty {
  text-align: center;
  color: #334155;
  font-size: 0.85rem;
  padding: 3rem 1rem;
  font-style: italic;
}

/* ── Oracle card ── */
.oracle-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.6rem;
  padding: 1rem 1.25rem;
  margin: 0.5rem 0 1rem;
  background: rgba(99, 102, 241, 0.06);
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: 0.75rem;
  text-align: center;
}

.oracle-icon {
  font-size: 1.25rem;
  color: #818cf8;
}

.oracle-suggestion {
  font-size: 0.82rem;
  color: #94a3b8;
  line-height: 1.55;
  margin: 0;
}

.oracle-use-btn {
  font-size: 0.72rem;
  font-family: inherit;
  color: #6366f1;
  background: none;
  border: 1px solid rgba(99, 102, 241, 0.3);
  border-radius: 100px;
  padding: 0.25rem 0.75rem;
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s;
}

.oracle-use-btn:hover {
  border-color: rgba(99, 102, 241, 0.6);
  color: #818cf8;
}

/* ── Bubbles ── */
.bubble-row {
  display: flex;
}

.bubble-row--self  { justify-content: flex-end; }
.bubble-row--other { justify-content: flex-start; }

.bubble {
  max-width: 72%;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  padding: 0.55rem 0.85rem;
  border-radius: 1rem;
  position: relative;
}

.bubble--self {
  background: rgba(99, 102, 241, 0.22);
  border: 1px solid rgba(99, 102, 241, 0.3);
  border-bottom-right-radius: 0.25rem;
}

.bubble--other {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-bottom-left-radius: 0.25rem;
}

.bubble-text {
  font-size: 0.88rem;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}

.bubble-time {
  font-size: 0.6rem;
  color: #475569;
  align-self: flex-end;
}

/* ── Input row ── */
.thread-input-row {
  display: flex;
  align-items: flex-end;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(10, 8, 20, 0.9);
  flex-shrink: 0;
}

.thread-input {
  flex: 1;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 0.75rem;
  color: #e2e8f0;
  font-family: inherit;
  font-size: 0.88rem;
  line-height: 1.5;
  padding: 0.55rem 0.85rem;
  resize: none;
  transition: border-color 0.15s;
  max-height: 120px;
  overflow-y: auto;
}

.thread-input:focus {
  outline: none;
  border-color: rgba(99, 102, 241, 0.5);
}

.thread-input:disabled { opacity: 0.5; }

.send-btn {
  width: 2.25rem;
  height: 2.25rem;
  flex-shrink: 0;
  border-radius: 50%;
  background: #6366f1;
  border: none;
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s, opacity 0.15s;
}

.send-btn:hover:not(:disabled) { background: #818cf8; }
.send-btn:disabled { opacity: 0.4; cursor: default; }

.send-btn svg { width: 15px; height: 15px; }

.send-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }
</style>
