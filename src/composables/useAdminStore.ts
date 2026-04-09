import { ref, readonly } from 'vue'
import { useAuthStore } from './useAuthStore'

// ── Types ────────────────────────────────────────────────────────────────────

export interface AdminUser {
  id: string
  email: string
  display_name: string | null
  created_at: string
  is_admin: boolean
  attachment_style: string | null
  defense_mechanism: string | null
  readiness_score: number | null
  archetype: string | null
  tone: string | null
  connected_providers: string[] | null
  connector_count: number
  karma_total: number
  matches_accepted: number
  matches_rejected: number
  received_accepts: number
  journal_entry_count: number
  messages_sent: number
  has_vibe_vector: boolean
  has_psychometrics: boolean
  has_spotify: boolean
  has_twitter: boolean
  has_gcal: boolean
  has_costar: boolean
  has_letterboxd: boolean
  has_steam: boolean
}

export interface FunnelStep {
  step: string
  count: number
  pct: number
}

export interface ConnectorStat {
  provider: string
  connected_count: number
  connection_rate_pct: number
  feedback_count: number
  avg_rating: number | null
  top_tags: string[]
}

export interface UsersPage {
  total: number
  page: number
  per_page: number
  users: AdminUser[]
}

// ── State ────────────────────────────────────────────────────────────────────

const users = ref<AdminUser[]>([])
const usersTotal = ref(0)
const usersPage = ref(1)
const funnel = ref<FunnelStep[]>([])
const connectors = ref<ConnectorStat[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

// ── Actions ──────────────────────────────────────────────────────────────────

async function fetchUsers(page = 1, perPage = 50) {
  const { apiFetch } = useAuthStore()
  loading.value = true
  error.value = null
  try {
    const data = await apiFetch<UsersPage>(
      `/api/analytics/users?page=${page}&per_page=${perPage}`
    )
    users.value = data.users
    usersTotal.value = data.total
    usersPage.value = data.page
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function fetchFunnel() {
  const { apiFetch } = useAuthStore()
  try {
    funnel.value = await apiFetch<FunnelStep[]>('/api/analytics/funnel')
  } catch (e: any) {
    error.value = e.message
  }
}

async function fetchConnectors() {
  const { apiFetch } = useAuthStore()
  try {
    connectors.value = await apiFetch<ConnectorStat[]>('/api/analytics/connectors')
  } catch (e: any) {
    error.value = e.message
  }
}

async function submitConnectorFeedback(provider: string, rating: number, tags: string[]) {
  const { apiFetch } = useAuthStore()
  await apiFetch('/api/analytics/feedback/connector', {
    method: 'POST',
    body: JSON.stringify({ provider, rating, tags }),
  })
}

async function logEvent(event: string, metadata: Record<string, unknown> = {}) {
  const { apiFetch } = useAuthStore()
  try {
    await apiFetch('/api/analytics/event', {
      method: 'POST',
      body: JSON.stringify({ event, metadata }),
    })
  } catch { /* non-blocking */ }
}

// ── Export ───────────────────────────────────────────────────────────────────

export function useAdminStore() {
  return {
    users: readonly(users),
    usersTotal: readonly(usersTotal),
    usersPage: readonly(usersPage),
    funnel: readonly(funnel),
    connectors: readonly(connectors),
    loading: readonly(loading),
    error: readonly(error),

    fetchUsers,
    fetchFunnel,
    fetchConnectors,
    submitConnectorFeedback,
    logEvent,
  }
}
