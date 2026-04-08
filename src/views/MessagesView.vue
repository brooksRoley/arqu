<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/composables/useAuthStore'
import { useMessageStore } from '@/composables/useMessageStore'

const router = useRouter()
const { isAuthenticated } = useAuthStore()
const { threads, fetchThreads } = useMessageStore()

if (!isAuthenticated.value) router.replace('/login')

onMounted(fetchThreads)

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

    <div v-if="threads.length === 0" class="inbox-empty">
      <span class="empty-icon">◈</span>
      <p>No conversations yet.<br />Accept a match to unlock messaging.</p>
      <router-link to="/game" class="inbox-cta">Go to matching →</router-link>
    </div>

    <div v-else class="thread-list">
      <router-link
        v-for="t in threads"
        :key="t.other_user_id"
        :to="`/messages/${t.other_user_id}`"
        class="thread-row"
        :class="{ 'thread-row--unread': t.unread_count > 0 }"
      >
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
</style>
