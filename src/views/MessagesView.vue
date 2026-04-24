<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/composables/useAuthStore'
import { useMessageStore } from '@/composables/useMessageStore'

const router = useRouter()
const { isAuthenticated } = useAuthStore()
const { threads, fetchThreads } = useMessageStore()

if (!isAuthenticated.value) router.replace('/login')

onMounted(fetchThreads)

// ── Bridge card (dismissible learn prompt) ─────────────────────
const BRIDGE_DISMISSED_KEY = 'channelzero-bridge-dismissed'
const bridgeDismissed = ref(localStorage.getItem(BRIDGE_DISMISSED_KEY) === '1')

function dismissBridge() {
  bridgeDismissed.value = true
  localStorage.setItem(BRIDGE_DISMISSED_KEY, '1')
}

function formatTime(iso: string | null): string {
  if (!iso) return ''
  const d = new Date(iso)
  const diffMs = Date.now() - d.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  if (diffMins < 60) return `${diffMins}m ago`
  const diffHrs = Math.floor(diffMins / 60)
  if (diffHrs < 24) return `${diffHrs}h ago`
  return d.toLocaleDateString([], { month: 'short', day: 'numeric' })
}
</script>

<template>
  <div class="inbox">
    <div class="inbox-header">
      <h1 class="inbox-title">Messages</h1>
      <p class="inbox-sub">Mutual matches only</p>
    </div>

    <!-- Bridge card: learn about your match signals -->
    <div v-if="threads.length > 0 && !bridgeDismissed" class="bridge-card">
      <button class="bridge-dismiss" @click="dismissBridge">&times;</button>
      <span class="bridge-icon">&#x2726;</span>
      <div class="bridge-text">
        <span class="bridge-title">Understand your signal overlap</span>
        <span class="bridge-desc">Learn how the Oracle matched you — attachment styles, sonic fingerprints, and behavioral vectors.</span>
      </div>
      <router-link to="/learn/how-matching-works" class="bridge-link">Read more &rarr;</router-link>
    </div>

    <div v-if="threads.length === 0" class="inbox-empty">
      <span class="empty-icon">◈</span>
      <p>No conversations yet.<br />Accept a match to unlock messaging.</p>
      <router-link to="/game" class="inbox-cta">Go to matching →</router-link>
    </div>

    <div v-else class="thread-list">
      <div
        v-for="t in threads"
        :key="t.other_user_id"
        class="thread-row"
        :class="{ 'thread-row--unread': t.unread_count > 0 }"
      >
        <router-link :to="`/messages/${t.other_user_id}`" class="thread-link">
          <div class="thread-avatar">
            {{ (t.other_user_name || '?')[0].toUpperCase() }}
          </div>
          <div class="thread-info">
            <div class="thread-top">
              <span class="thread-name">{{ t.other_user_name }}</span>
              <span class="thread-time">{{ formatTime(t.last_message_at) }}</span>
            </div>
            <div class="thread-preview">
              <span class="preview-text">{{ t.last_message }}</span>
              <span v-if="t.unread_count > 0" class="unread-badge">{{ t.unread_count }}</span>
            </div>
          </div>
        </router-link>
        <router-link
          :to="`/reveal/${t.other_user_id}`"
          class="signal-story-link"
          @click.stop
        >Signal Story</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.inbox {
  min-height: calc(100vh - 3rem);
  background: #08060e;
  color: #e2e8f0;
  padding: 2rem 1rem;
  max-width: 600px;
  margin: 0 auto;
}

.inbox-header {
  margin-bottom: 2rem;
}

.inbox-title {
  font-size: 1.6rem;
  font-weight: 700;
  margin: 0 0 0.25rem;
}

.inbox-sub {
  font-size: 0.8rem;
  color: #475569;
  margin: 0;
}

.inbox-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  text-align: center;
  padding: 4rem 1rem;
  color: #475569;
  font-size: 0.9rem;
  line-height: 1.6;
}

.empty-icon {
  font-size: 2rem;
  color: #334155;
}

.inbox-cta {
  font-size: 0.82rem;
  color: #6366f1;
  text-decoration: none;
  border: 1px solid rgba(99, 102, 241, 0.3);
  border-radius: 100px;
  padding: 0.35rem 0.9rem;
  transition: border-color 0.15s, color 0.15s;
}

.inbox-cta:hover {
  border-color: rgba(99, 102, 241, 0.6);
  color: #818cf8;
}

.thread-list {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.thread-row {
  display: flex;
  align-items: center;
  gap: 0.9rem;
  padding: 0.9rem 0.75rem;
  border-radius: 0.75rem;
  text-decoration: none;
  color: inherit;
  transition: background 0.15s;
}

.thread-row:hover {
  background: rgba(255, 255, 255, 0.04);
}

.thread-link {
  display: flex;
  align-items: center;
  gap: 0.9rem;
  flex: 1;
  text-decoration: none;
  color: inherit;
}

.signal-story-link {
  font-size: 11px;
  color: #a78bfa;
  text-decoration: none;
  padding: 4px 10px;
  border-radius: 6px;
  white-space: nowrap;
  transition: background 0.15s, color 0.15s;
}

.signal-story-link:hover {
  background: rgba(139, 92, 246, 0.1);
  color: #c4b5fd;
}

.thread-row--unread .thread-name {
  color: #e2e8f0;
  font-weight: 600;
}

.thread-avatar {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 50%;
  background: rgba(99, 102, 241, 0.2);
  border: 1px solid rgba(99, 102, 241, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  font-weight: 600;
  color: #818cf8;
  flex-shrink: 0;
}

.thread-info {
  flex: 1;
  min-width: 0;
}

.thread-top {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 0.2rem;
}

.thread-name {
  font-size: 0.9rem;
  color: #cbd5e1;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.thread-time {
  font-size: 0.68rem;
  color: #334155;
  flex-shrink: 0;
  margin-left: 0.5rem;
}

.thread-preview {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.preview-text {
  font-size: 0.78rem;
  color: #475569;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
}

.unread-badge {
  flex-shrink: 0;
  background: #6366f1;
  color: #fff;
  font-size: 0.65rem;
  font-weight: 700;
  border-radius: 100px;
  min-width: 1.1rem;
  height: 1.1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 0.25rem;
}

/* ── Bridge card ── */
.bridge-card {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 1rem 1.25rem;
  margin-bottom: 1.5rem;
  background: rgba(99, 102, 241, 0.06);
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: 0.75rem;
}

.bridge-dismiss {
  position: absolute;
  top: 0.5rem;
  right: 0.6rem;
  background: none;
  border: none;
  color: #475569;
  font-size: 1rem;
  cursor: pointer;
  line-height: 1;
  padding: 0;
}

.bridge-dismiss:hover { color: #94a3b8; }

.bridge-icon {
  font-size: 1.2rem;
  color: #6366f1;
  flex-shrink: 0;
  margin-top: 0.1rem;
}

.bridge-text {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  flex: 1;
}

.bridge-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: #c4b5fd;
}

.bridge-desc {
  font-size: 0.75rem;
  color: #64748b;
  line-height: 1.5;
}

.bridge-link {
  flex-shrink: 0;
  align-self: center;
  font-size: 0.75rem;
  color: #6366f1;
  text-decoration: none;
  white-space: nowrap;
  transition: color 0.15s;
}

.bridge-link:hover { color: #818cf8; }
</style>
