import { ref, readonly } from 'vue'
import { useAuthStore } from './useAuthStore'

// ── Types ────────────────────────────────────────────────────────────────────

export interface Message {
  id: string
  sender_id: string
  recipient_id: string
  body: string
  read_at: string | null
  created_at: string
}

export interface ThreadSummary {
  other_user_id: string
  other_user_name: string
  last_message: string | null
  last_message_at: string | null
  unread_count: number
}

// ── Singleton state ──────────────────────────────────────────────────────────

const unreadCount = ref(0)
const threads = ref<ThreadSummary[]>([])
const activeThread = ref<Message[]>([])
const activeUserId = ref<string | null>(null)
const sending = ref(false)
const loadingThread = ref(false)
const error = ref<string | null>(null)

let pollTimer: ReturnType<typeof setInterval> | null = null

// ── Actions ──────────────────────────────────────────────────────────────────

async function fetchUnread() {
  const { apiFetch, isAuthenticated } = useAuthStore()
  if (!isAuthenticated.value) return
  try {
    const data = await apiFetch<{ unread: number }>('/api/messages/unread')
    unreadCount.value = data.unread
  } catch { /* silent — badge is non-critical */ }
}

async function fetchThreads() {
  const { apiFetch } = useAuthStore()
  try {
    threads.value = await apiFetch<ThreadSummary[]>('/api/messages/threads')
    unreadCount.value = threads.value.reduce((s, t) => s + t.unread_count, 0)
  } catch (e: any) {
    error.value = e.message
  }
}

async function openThread(otherUserId: string) {
  const { apiFetch } = useAuthStore()
  activeUserId.value = otherUserId
  loadingThread.value = true
  error.value = null
  try {
    const msgs = await apiFetch<Message[]>(`/api/messages/thread/${otherUserId}`)
    activeThread.value = msgs
    // Mark as read — unread count will drop on next poll
    unreadCount.value = Math.max(0, unreadCount.value - threads.value.find(t => t.other_user_id === otherUserId)?.unread_count ?? 0)
  } catch (e: any) {
    error.value = e.message
  } finally {
    loadingThread.value = false
  }
}

async function pollThread() {
  if (!activeUserId.value) return
  const { apiFetch } = useAuthStore()
  try {
    const msgs = await apiFetch<Message[]>(`/api/messages/thread/${activeUserId.value}`)
    activeThread.value = msgs
  } catch { /* silent poll */ }
}

async function sendMessage(recipientId: string, body: string): Promise<Message | null> {
  const { apiFetch } = useAuthStore()
  sending.value = true
  error.value = null
  try {
    const msg = await apiFetch<Message>('/api/messages/send', {
      method: 'POST',
      body: JSON.stringify({ recipient_id: recipientId, body }),
    })
    activeThread.value = [...activeThread.value, msg]
    return msg
  } catch (e: any) {
    error.value = e.message
    return null
  } finally {
    sending.value = false
  }
}

function startPolling(intervalMs = 5000) {
  if (pollTimer) return
  pollTimer = setInterval(() => {
    pollThread()
    fetchUnread()
  }, intervalMs)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

function clearThread() {
  activeThread.value = []
  activeUserId.value = null
  stopPolling()
}

// ── Export ───────────────────────────────────────────────────────────────────

export function useMessageStore() {
  return {
    unreadCount: readonly(unreadCount),
    threads: readonly(threads),
    activeThread: readonly(activeThread),
    activeUserId: readonly(activeUserId),
    sending: readonly(sending),
    loadingThread: readonly(loadingThread),
    error: readonly(error),

    fetchUnread,
    fetchThreads,
    openThread,
    sendMessage,
    startPolling,
    stopPolling,
    clearThread,
  }
}
