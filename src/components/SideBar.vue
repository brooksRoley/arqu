<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { RouterLink, useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/composables/useAuthStore'
import { usePollStore } from '@/composables/usePollStore'
import { useVibeStore } from '@/composables/useVibeStore'
import { useMessageStore } from '@/composables/useMessageStore'
import ConnectorPanel from '@/components/ConnectorPanel.vue'

const router = useRouter()
const route = useRoute()
const { isAuthenticated, user } = useAuthStore()
const { token: pollToken } = usePollStore()
const { oauthState } = useVibeStore()
const { unreadCount } = useMessageStore()

const collapsed = ref(false)
const mobileOpen = ref(false)

// Close on route change (mobile)
watch(() => route.path, () => { mobileOpen.value = false })

// Close mobile sidebar on outside click
function handleOutside(e: MouseEvent) {
  if (!mobileOpen.value) return
  const el = document.querySelector('.sidebar')
  if (el && !el.contains(e.target as Node)) mobileOpen.value = false
}

onMounted(() => document.addEventListener('click', handleOutside))
onUnmounted(() => document.removeEventListener('click', handleOutside))

// ── Onboarding state ──────────────────────────────────────────────

const ONBOARDING_KEY = 'channelzero-onboarding'
interface OnboardingState {
  poll: boolean; calibrate: boolean; psychoanalysis: boolean; intake: boolean; completed: boolean
}
function loadOnboarding(): OnboardingState {
  try {
    const raw = localStorage.getItem(ONBOARDING_KEY)
    if (raw) return JSON.parse(raw)
  } catch {}
  return { poll: false, calibrate: false, psychoanalysis: false, intake: false, completed: false }
}
const onboarding = ref<OnboardingState>(loadOnboarding())

watch(pollToken, (t) => {
  if (t && !onboarding.value.poll) {
    onboarding.value.poll = true
    const s = loadOnboarding(); s.poll = true
    localStorage.setItem(ONBOARDING_KEY, JSON.stringify(s))
  }
}, { immediate: true })

// ── Quest steps ───────────────────────────────────────────────────

interface QuestStep {
  key: string; label: string; icon: string; color: string; route: string; done: boolean
}

const questSteps = computed<QuestStep[]>(() => {
  const anyConnected = Object.values(oauthState.value).some(p => p.connected)
  return [
    { key: 'attune',   label: 'Attunement',  icon: '✦', color: '#a78bfa', route: '/',              done: !!pollToken.value },
    { key: 'signal',   label: 'Signal',       icon: '◉', color: '#22c55e', route: '/calibrate',     done: anyConnected },
    { key: 'confess',  label: 'Confession',   icon: '◈', color: '#38bdf8', route: '/intake',        done: onboarding.value.intake },
    { key: 'resonate', label: 'Resonance',    icon: '⬡', color: '#f59e0b', route: '/game',          done: onboarding.value.completed },
  ]
})

const currentQuestIdx = computed(() => questSteps.value.findIndex(s => !s.done))
const questProgress = computed(() => {
  const done = questSteps.value.filter(s => s.done).length
  return done / questSteps.value.length
})

// ── Zone navigation ───────────────────────────────────────────────

interface NavItem {
  label: string; icon: string; route: string; badge?: number; zone: string
}

const navItems = computed<NavItem[]>(() => {
  const items: NavItem[] = [
    // The Nexus — guidance & progress
    { label: 'Home',          icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-4 0a1 1 0 01-1-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 01-1 1h-2z', route: '/', zone: 'nexus' },
    { label: 'Universe',     icon: 'M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z', route: '/universe', zone: 'nexus' },
    { label: 'Check-in',     icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4', route: '/checkin', zone: 'nexus' },

    // The Forge — creation tools
    { label: 'Studio',       icon: 'M2 3h20v14H2zM8 21h8M12 17v4M7 8h1m4-1v2m4-1h1', route: '/studio', zone: 'forge' },
    { label: 'Reader',       icon: 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253z', route: '/reader', zone: 'forge' },
    { label: 'Audio',        icon: 'M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2z', route: '/audio', zone: 'forge' },
    { label: 'Journal',      icon: 'M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z', route: '/journal', zone: 'forge' },

    // The Archive — connectors & data
    { label: 'Calibrate',    icon: 'M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4', route: '/calibrate', zone: 'archive' },
    { label: 'Analysis',     icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z', route: '/psychoanalysis', zone: 'archive' },
    { label: 'Messages',     icon: 'M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z', route: '/messages', badge: unreadCount.value > 0 ? unreadCount.value : undefined, zone: 'archive' },
  ]
  return items.filter(i => {
    if (i.route === '/universe' && !isAuthenticated.value) return false
    if (['/checkin', '/journal', '/calibrate', '/psychoanalysis', '/messages'].includes(i.route) && !isAuthenticated.value) return false
    return true
  })
})

const zones = computed(() => {
  const map = new Map<string, { label: string; items: NavItem[] }>()
  const zoneMeta: Record<string, string> = {
    nexus:   'Nexus',
    forge:   'Forge',
    archive: 'Archive',
  }
  for (const item of navItems.value) {
    if (!map.has(item.zone)) map.set(item.zone, { label: zoneMeta[item.zone] || item.zone, items: [] })
    map.get(item.zone)!.items.push(item)
  }
  return Array.from(map.values())
})

// ── Sessions ──────────────────────────────────────────────────────

interface SessionLink { route: string; label: string; icon: string }

const sessionLinks = computed<SessionLink[]>(() => {
  if (!pollToken.value) return []
  const themeSessions: Record<string, SessionLink[]> = {
    dreamlike: [
      { route: '/webaudio', label: 'Star Tunnel', icon: '✦' },
      { route: '/zeromind', label: 'Zeromind',    icon: '🔮' },
      { route: '/spiral',   label: 'Spiral',      icon: '🌀' },
      { route: '/trance',   label: 'Tone Engine', icon: '🎧' },
    ],
    electric: [
      { route: '/zeromind', label: 'Zeromind',    icon: '🔮' },
      { route: '/webaudio', label: 'Star Tunnel', icon: '✦' },
      { route: '/spiral',   label: 'Spiral',      icon: '🌀' },
      { route: '/trance',   label: 'Tone Engine', icon: '🎧' },
    ],
    void: [
      { route: '/spiral',   label: 'Spiral',      icon: '🌀' },
      { route: '/trance',   label: 'Tone Engine', icon: '🎧' },
      { route: '/webaudio', label: 'Star Tunnel', icon: '✦' },
      { route: '/zeromind', label: 'Zeromind',    icon: '🔮' },
    ],
    organic: [
      { route: '/trance',   label: 'Tone Engine', icon: '🎧' },
      { route: '/webaudio', label: 'Star Tunnel', icon: '✦' },
      { route: '/spiral',   label: 'Spiral',      icon: '🌀' },
      { route: '/zeromind', label: 'Zeromind',    icon: '🔮' },
    ],
    liminal: [
      { route: '/webaudio', label: 'Star Tunnel', icon: '✦' },
      { route: '/zeromind', label: 'Zeromind',    icon: '🔮' },
      { route: '/spiral',   label: 'Spiral',      icon: '🌀' },
      { route: '/trance',   label: 'Tone Engine', icon: '🎧' },
    ],
  }
  return themeSessions[pollToken.value.theme] || themeSessions.liminal
})

// ── Display name ──────────────────────────────────────────────────

const displayName = computed(() =>
  user.value?.display_name || user.value?.email?.split('@')[0] || null
)

const accent = computed(() => pollToken.value?.palette?.accent || '#a78bfa')
</script>

<template>
  <!-- Mobile toggle button -->
  <button
    class="sidebar-toggle"
    :class="{ 'sidebar-toggle--open': mobileOpen }"
    @click.stop="mobileOpen = !mobileOpen"
    aria-label="Toggle sidebar"
  >
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
      <template v-if="!mobileOpen">
        <line x1="3" y1="6" x2="21" y2="6"/>
        <line x1="3" y1="12" x2="21" y2="12"/>
        <line x1="3" y1="18" x2="21" y2="18"/>
      </template>
      <template v-else>
        <line x1="18" y1="6" x2="6" y2="18"/>
        <line x1="6" y1="6" x2="18" y2="18"/>
      </template>
    </svg>
  </button>

  <!-- Mobile backdrop -->
  <Teleport to="body">
    <div v-if="mobileOpen" class="sidebar-backdrop" @click="mobileOpen = false"></div>
  </Teleport>

  <aside
    :class="[
      'sidebar',
      {
        'sidebar--collapsed': collapsed,
        'sidebar--mobile-open': mobileOpen,
      }
    ]"
    @click.stop
  >
    <!-- Logo / branding -->
    <div class="sb-brand">
      <RouterLink to="/" class="sb-logo">
        <span class="sb-logo-mark" :style="{ color: accent }">CZ</span>
        <span v-if="!collapsed" class="sb-logo-text">Channel Zero</span>
      </RouterLink>
      <button class="sb-collapse-btn" @click="collapsed = !collapsed" :aria-label="collapsed ? 'Expand sidebar' : 'Collapse sidebar'">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <polyline v-if="!collapsed" points="15 18 9 12 15 6"/>
          <polyline v-else points="9 18 15 12 9 6"/>
        </svg>
      </button>
    </div>

    <!-- User badge -->
    <div v-if="isAuthenticated && displayName && !collapsed" class="sb-user">
      <span class="sb-user-avatar" :style="{ background: accent }">{{ displayName[0].toUpperCase() }}</span>
      <span class="sb-user-name">{{ displayName }}</span>
    </div>

    <!-- Quest Progress (The HUD) -->
    <div v-if="isAuthenticated && currentQuestIdx !== -1" class="sb-section">
      <span v-if="!collapsed" class="sb-section-label">Quest</span>
      <div class="sb-quest">
        <div v-if="!collapsed" class="sb-quest-bar">
          <div class="sb-quest-fill" :style="{ width: `${questProgress * 100}%`, background: accent }"></div>
        </div>
        <div class="sb-quest-steps">
          <RouterLink
            v-for="(s, i) in questSteps"
            :key="s.key"
            :to="s.route"
            class="sb-quest-step"
            :class="{
              'sb-quest-step--done': s.done,
              'sb-quest-step--current': i === currentQuestIdx,
              'sb-quest-step--locked': i > currentQuestIdx && !s.done,
            }"
            :title="s.label"
          >
            <span class="sb-quest-icon" :style="s.done || i === currentQuestIdx ? { color: s.color } : {}">{{ s.icon }}</span>
            <span v-if="!collapsed" class="sb-quest-label">{{ s.label }}</span>
            <span v-if="!collapsed && s.done" class="sb-quest-check">&#x2713;</span>
            <span v-if="!collapsed && i === currentQuestIdx && !s.done" class="sb-quest-you">you are here</span>
          </RouterLink>
        </div>
      </div>
    </div>

    <!-- Zone navigation -->
    <div v-for="z in zones" :key="z.label" class="sb-section">
      <span v-if="!collapsed" class="sb-section-label">{{ z.label }}</span>
      <nav class="sb-nav">
        <RouterLink
          v-for="item in z.items"
          :key="item.route"
          :to="item.route"
          class="sb-nav-item"
          active-class="sb-nav-item--active"
          :title="collapsed ? item.label : undefined"
        >
          <svg class="sb-nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" v-html="item.icon"></svg>
          <span v-if="!collapsed" class="sb-nav-label">{{ item.label }}</span>
          <span v-if="item.badge && !collapsed" class="sb-nav-badge">{{ item.badge > 9 ? '9+' : item.badge }}</span>
          <span v-if="item.badge && collapsed" class="sb-nav-badge sb-nav-badge--dot"></span>
        </RouterLink>
      </nav>
    </div>

    <!-- Sessions (The Wilds) -->
    <div v-if="sessionLinks.length > 0" class="sb-section">
      <span v-if="!collapsed" class="sb-section-label">Sessions</span>
      <nav class="sb-nav">
        <RouterLink
          v-for="s in sessionLinks"
          :key="s.route"
          :to="s.route"
          class="sb-nav-item"
          active-class="sb-nav-item--active"
          :title="collapsed ? s.label : undefined"
        >
          <span class="sb-session-icon">{{ s.icon }}</span>
          <span v-if="!collapsed" class="sb-nav-label">{{ s.label }}</span>
        </RouterLink>
      </nav>
    </div>

    <!-- Connectors (compact) -->
    <div v-if="isAuthenticated && !collapsed" class="sb-section sb-section--connectors">
      <ConnectorPanel />
    </div>

    <!-- Bottom spacer -->
    <div class="sb-spacer"></div>
  </aside>
</template>

<style scoped>
/* ── Sidebar shell ── */
.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  width: 240px;
  background: rgba(8, 8, 18, 0.95);
  backdrop-filter: blur(16px);
  border-right: 1px solid rgba(255, 255, 255, 0.06);
  z-index: 900;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-width: thin;
  scrollbar-color: #1e293b transparent;
  transition: width 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.sidebar::-webkit-scrollbar { width: 4px; }
.sidebar::-webkit-scrollbar-track { background: transparent; }
.sidebar::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 4px; }

.sidebar--collapsed { width: 56px; }

/* ── Mobile ── */
.sidebar-toggle {
  display: none;
  position: fixed;
  top: 0.6rem;
  left: 0.6rem;
  z-index: 1100;
  width: 36px;
  height: 36px;
  background: rgba(10, 10, 20, 0.9);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 0.4rem;
  color: #94a3b8;
  cursor: pointer;
  padding: 0;
  align-items: center;
  justify-content: center;
}

.sidebar-toggle svg { width: 18px; height: 18px; }
.sidebar-toggle:hover { color: #e2e8f0; border-color: rgba(255,255,255,0.2); }

.sidebar-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 899;
}

@media (max-width: 768px) {
  .sidebar {
    transform: translateX(-100%);
    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }
  .sidebar--mobile-open { transform: translateX(0); }
  .sidebar--collapsed { width: 240px; } /* ignore collapse on mobile */
  .sidebar-toggle { display: flex; }
}

/* ── Brand ── */
.sb-brand {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.85rem 0.75rem 0.5rem;
  min-height: 48px;
}

.sb-logo {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
  color: #e2e8f0;
  overflow: hidden;
}

.sb-logo-mark {
  font-size: 1rem;
  font-weight: 800;
  letter-spacing: -0.05em;
  flex-shrink: 0;
}

.sb-logo-text {
  font-size: 0.85rem;
  font-weight: 600;
  white-space: nowrap;
  letter-spacing: -0.02em;
}

.sb-collapse-btn {
  background: none;
  border: none;
  color: #475569;
  cursor: pointer;
  padding: 0.2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 0.25rem;
  transition: color 0.15s;
  flex-shrink: 0;
}

.sb-collapse-btn svg { width: 14px; height: 14px; }
.sb-collapse-btn:hover { color: #94a3b8; }

/* ── User ── */
.sb-user {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0.75rem 0.75rem;
}

.sb-user-avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.65rem;
  font-weight: 700;
  color: #0f0f1a;
  flex-shrink: 0;
}

.sb-user-name {
  font-size: 0.72rem;
  color: #64748b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ── Sections ── */
.sb-section {
  padding: 0.5rem 0.6rem;
}

.sb-section-label {
  font-size: 0.58rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #334155;
  font-weight: 600;
  display: block;
  padding: 0 0.35rem 0.35rem;
}

.sb-section--connectors {
  padding: 0 0.35rem;
}

.sb-section--connectors :deep(.connector-panel) {
  margin: 0;
  padding: 0.75rem;
  border: none;
  background: transparent;
}

/* ── Navigation items ── */
.sb-nav {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.sb-nav-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0.5rem;
  border-radius: 0.4rem;
  color: #64748b;
  text-decoration: none;
  font-size: 0.78rem;
  transition: color 0.12s, background 0.12s;
  position: relative;
}

.sb-nav-item:hover {
  color: #e2e8f0;
  background: rgba(255, 255, 255, 0.05);
}

.sb-nav-item--active {
  color: #e2e8f0;
  background: rgba(99, 102, 241, 0.15);
}

.sb-nav-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.sb-nav-label {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sb-nav-badge {
  font-size: 0.55rem;
  font-weight: 700;
  background: #6366f1;
  color: #fff;
  border-radius: 100px;
  min-width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
  flex-shrink: 0;
}

.sb-nav-badge--dot {
  width: 6px;
  height: 6px;
  min-width: 6px;
  padding: 0;
  position: absolute;
  top: 4px;
  right: 4px;
}

.sb-session-icon {
  width: 16px;
  text-align: center;
  font-size: 0.85rem;
  flex-shrink: 0;
}

/* ── Quest progress ── */
.sb-quest {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.sb-quest-bar {
  height: 3px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 2px;
  overflow: hidden;
  margin: 0 0.35rem 0.15rem;
}

.sb-quest-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.5s ease;
}

.sb-quest-steps {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.sb-quest-step {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.35rem 0.5rem;
  border-radius: 0.35rem;
  text-decoration: none;
  color: #475569;
  font-size: 0.75rem;
  transition: color 0.12s, background 0.12s;
  position: relative;
}

.sb-quest-step:hover {
  background: rgba(255, 255, 255, 0.04);
  color: #94a3b8;
}

.sb-quest-step--done {
  color: #64748b;
}

.sb-quest-step--current {
  color: #e2e8f0;
  background: rgba(255, 255, 255, 0.04);
}

.sb-quest-step--locked {
  opacity: 0.4;
}

.sb-quest-icon {
  font-size: 0.9rem;
  flex-shrink: 0;
  width: 16px;
  text-align: center;
}

.sb-quest-label {
  flex: 1;
  white-space: nowrap;
}

.sb-quest-check {
  font-size: 0.6rem;
  color: #22c55e;
}

.sb-quest-you {
  font-size: 0.55rem;
  color: #a78bfa;
  background: rgba(167, 139, 250, 0.1);
  padding: 0.1rem 0.35rem;
  border-radius: 100px;
  white-space: nowrap;
}

/* ── Spacer ── */
.sb-spacer { flex: 1; }
</style>
