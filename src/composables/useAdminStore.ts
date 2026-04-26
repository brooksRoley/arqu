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
  has_github: boolean
  has_youtube: boolean
  has_reddit: boolean
  has_instagram: boolean
  has_tiktok: boolean
  has_strava: boolean
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

export interface SpotifyProfile {
  user_id: string
  email: string
  display_name: string | null
  top_artists: string[]
  genres: string[]
  audio_avg: Record<string, number>
}

export interface PsychometricProfile {
  user_id: string
  email: string
  display_name: string | null
  love_language: string | null
  sociosexual_orientation: string | null
  values_cluster: string | null
  narrative: string | null
  ipip_neo_scores: Record<string, number> | null
  ecr_r_scores: Record<string, number> | null
  created_at: string
}

export interface MatchTrends {
  seven_day: { players: number; matched: number; rate_pct: number }
  thirty_day: { players: number; matched: number; rate_pct: number }
}

export interface ArchetypeCount {
  archetype: string
  count: number
}

export interface AttachmentCount {
  style: string
  count: number
}

export interface ConnectorDepthBucket {
  connectors: number
  count: number
}

// ── State ────────────────────────────────────────────────────────────────────

const users = ref<AdminUser[]>([])
const usersTotal = ref(0)
const usersPage = ref(1)
const funnel = ref<FunnelStep[]>([])
const connectors = ref<ConnectorStat[]>([])
const matchTrends = ref<MatchTrends | null>(null)
const spotifyProfiles = ref<SpotifyProfile[]>([])
const spotifyTotal = ref(0)
const spotifyPage = ref(1)
const psychProfiles = ref<PsychometricProfile[]>([])
const psychTotal = ref(0)
const psychPage = ref(1)
const archetypes = ref<ArchetypeCount[]>([])
const archetypesTotal = ref(0)
const attachmentStyles = ref<AttachmentCount[]>([])
const attachmentTotal = ref(0)
const connectorDepth = ref<ConnectorDepthBucket[]>([])
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

async function fetchMatchTrends() {
  const { apiFetch } = useAuthStore()
  try {
    matchTrends.value = await apiFetch<MatchTrends>('/api/analytics/match-trends')
  } catch (e: any) {
    error.value = e.message
  }
}

async function fetchSpotifyProfiles(page = 1, perPage = 50) {
  const { apiFetch } = useAuthStore()
  try {
    const data = await apiFetch<{ total: number; page: number; profiles: SpotifyProfile[] }>(
      `/api/analytics/spotify-profiles?page=${page}&per_page=${perPage}`
    )
    spotifyProfiles.value = data.profiles
    spotifyTotal.value = data.total
    spotifyPage.value = data.page
  } catch (e: any) {
    error.value = e.message
  }
}

async function fetchPsychProfiles(page = 1, perPage = 50) {
  const { apiFetch } = useAuthStore()
  try {
    const data = await apiFetch<{ total: number; page: number; profiles: PsychometricProfile[] }>(
      `/api/analytics/psychometrics?page=${page}&per_page=${perPage}`
    )
    psychProfiles.value = data.profiles
    psychTotal.value = data.total
    psychPage.value = data.page
  } catch (e: any) {
    error.value = e.message
  }
}

async function fetchArchetypes() {
  const { apiFetch } = useAuthStore()
  try {
    const data = await apiFetch<{ total: number; archetypes: ArchetypeCount[] }>('/api/analytics/archetypes')
    archetypes.value = data.archetypes
    archetypesTotal.value = data.total
  } catch (e: any) { error.value = e.message }
}

async function fetchAttachmentStyles() {
  const { apiFetch } = useAuthStore()
  try {
    const data = await apiFetch<{ total: number; styles: AttachmentCount[] }>('/api/analytics/attachment-styles')
    attachmentStyles.value = data.styles
    attachmentTotal.value = data.total
  } catch (e: any) { error.value = e.message }
}

async function fetchConnectorDepth() {
  const { apiFetch } = useAuthStore()
  try {
    const data = await apiFetch<{ histogram: ConnectorDepthBucket[] }>('/api/analytics/connector-depth')
    connectorDepth.value = data.histogram
  } catch (e: any) { error.value = e.message }
}

async function fetchUserConnectors(userId: string): Promise<Record<string, any>> {
  const { apiFetch } = useAuthStore()
  const data = await apiFetch<{ connectors: Record<string, any> }>(
    `/api/analytics/users/${userId}/connectors`
  )
  return data.connectors
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
    matchTrends: readonly(matchTrends),
    spotifyProfiles: readonly(spotifyProfiles),
    spotifyTotal: readonly(spotifyTotal),
    spotifyPage: readonly(spotifyPage),
    psychProfiles: readonly(psychProfiles),
    psychTotal: readonly(psychTotal),
    psychPage: readonly(psychPage),
    archetypes: readonly(archetypes),
    archetypesTotal: readonly(archetypesTotal),
    attachmentStyles: readonly(attachmentStyles),
    attachmentTotal: readonly(attachmentTotal),
    connectorDepth: readonly(connectorDepth),
    loading: readonly(loading),
    error: readonly(error),

    fetchUsers,
    fetchFunnel,
    fetchConnectors,
    fetchMatchTrends,
    fetchSpotifyProfiles,
    fetchPsychProfiles,
    fetchArchetypes,
    fetchAttachmentStyles,
    fetchConnectorDepth,
    fetchUserConnectors,
    submitConnectorFeedback,
    logEvent,
  }
}
