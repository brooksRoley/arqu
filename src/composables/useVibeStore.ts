import { ref, computed, readonly } from 'vue'
import { useAuthStore } from './useAuthStore'

// ── Types ────────────────────────────────────────────────────────────────────

export interface SpotifyProfile {
  top_artists: string[]
  genres: string[]
  audio_avg: {
    valence?: number
    danceability?: number
    energy?: number
    acousticness?: number
    tempo?: number
  }
}

export interface ProviderState {
  connected: boolean
  lastSync: string | null
}

export interface OAuthState {
  spotify: ProviderState
  twitter: ProviderState
  google: ProviderState
  strava: ProviderState
  costar: ProviderState
  letterboxd: ProviderState
  steam: ProviderState
  github: ProviderState
  youtube: ProviderState
  reddit: ProviderState
  instagram: ProviderState
  tiktok: ProviderState
}

export interface SonicOverlap {
  shared_genres: readonly string[]
  shared_artists: readonly string[]
  their_top_genres: readonly string[]
  valence_delta: number
  energy_delta: number
}

export interface TwitterOverlap {
  both_connected: boolean
  communication_style_match: boolean
  shared_language: boolean | null
  their_username: string | null
}

export interface StravaOverlap {
  both_connected: boolean
  shared_activities: readonly string[]
  their_activity_types: readonly string[]
}

export interface OracleInsight {
  empathy_index: number | null
  isolation_metric: number | null
  fatalism_score: number | null
  masochism_curve: number | null
  oracle_rationale: string | null
}

export interface OracleCoordinate {
  synthesized: boolean
  coordinate?: {
    empathy_index: number
    isolation_metric: number
    fatalism_score: number
    masochism_curve: number
    oracle_rationale: string
    suggested_community_action: string
  }
  synthesized_at?: string
}

export interface VibeMatch {
  user_id: string
  display_name: string
  avatar_url: string | null
  attachment_style: string | null
  defense_mechanism: string | null
  similarity: number
  match_reason: string
  sonic_overlap: SonicOverlap | null
  twitter_overlap: TwitterOverlap | null
  strava_overlap: StravaOverlap | null
  oracle_insight: OracleInsight | null
  they_accepted: boolean
  my_action: 'accept' | 'reject' | null
}

export interface InteractResult {
  recorded: boolean
  mutual_match: boolean
  target_id: string
  action: string
}

export interface FittingData {
  body_type: 'female' | 'male'
  height: number
  build: number
  chest: number
  waist: number
  hips: number
  shoulders: number
  skin_color: string
  skin_shadow: string
  hair_color: string
  hair_length: 'short' | 'medium' | 'long'
  suit_color: string
  suit_color_dark: string
  top_style?: string
  rise?: string
  coverage?: string
  top?: string
  bottom?: string
  wetsuit?: string
}

export interface RevealUserData {
  display_name: string | null
  fitting_self: FittingData | null
  fitting_ideal: FittingData | null
  spotify_data: Record<string, unknown> | null
  twitter_data: Record<string, unknown> | null
  strava_data: Record<string, unknown> | null
  steam_data: Record<string, unknown> | null
  oracle_coordinate: Record<string, unknown> | null
  attachment_style: string | null
  defense_mechanism: string | null
  has_spotify: boolean
  has_twitter: boolean
  has_strava: boolean
  has_steam: boolean
  has_oracle: boolean
}

export interface RevealPsychometrics {
  ipip_neo_scores: Record<string, number> | null
  ecr_r_scores: Record<string, number> | null
  love_language: string | null
  sociosexual_orientation: string | null
  values_cluster: string | null
}

export interface RevealData {
  similarity: number
  match_reason: string
  self: RevealUserData | null
  match: RevealUserData | null
  psychometrics: {
    self: RevealPsychometrics | null
    match: RevealPsychometrics | null
  }
}

// ── Storage key ──────────────────────────────────────────────────────────────

const OAUTH_KEY = 'channelzero-oauth'
const API = import.meta.env.VITE_API_URL || ''

// ── Module-level singleton state ─────────────────────────────────────────────

function defaultOAuthState(): OAuthState {
  return {
    spotify:    { connected: false, lastSync: null },
    twitter:    { connected: false, lastSync: null },
    google:     { connected: false, lastSync: null },
    strava:     { connected: false, lastSync: null },
    costar:     { connected: false, lastSync: null },
    letterboxd: { connected: false, lastSync: null },
    steam:      { connected: false, lastSync: null },
    github:     { connected: false, lastSync: null },
    youtube:    { connected: false, lastSync: null },
    reddit:     { connected: false, lastSync: null },
    instagram:  { connected: false, lastSync: null },
    tiktok:     { connected: false, lastSync: null },
  }
}

function loadPersistedState(): OAuthState {
  try {
    const raw = localStorage.getItem(OAUTH_KEY)
    if (raw) return { ...defaultOAuthState(), ...JSON.parse(raw) }
  } catch { /* ignore */ }
  return defaultOAuthState()
}

const oauthState = ref<OAuthState>(loadPersistedState())
const matches = ref<VibeMatch[]>([])
const matchesLoading = ref(false)
const matchesError = ref<string | null>(null)
const mutualMatchUserId = ref<string | null>(null)
const oracleCoordinate = ref<OracleCoordinate | null>(null)

// ── Derived ──────────────────────────────────────────────────────────────────

const isMatchReady = computed(() => oauthState.value.spotify.connected)

// ── Helpers ──────────────────────────────────────────────────────────────────

function persist() {
  localStorage.setItem(OAUTH_KEY, JSON.stringify(oauthState.value))
}

// ── Actions ──────────────────────────────────────────────────────────────────

/**
 * Hydrate connected state from the backend (source of truth).
 * Called on app init when the user is authenticated.
 */
async function syncConnectors() {
  const { apiFetch, isAuthenticated } = useAuthStore()
  if (!isAuthenticated.value) return
  try {
    const providers = await apiFetch<string[]>('/api/auth/connectors')
    for (const p of providers) {
      if (p in oauthState.value) {
        const key = p as keyof OAuthState
        if (!oauthState.value[key].connected) {
          oauthState.value[key] = { connected: true, lastSync: new Date().toISOString() }
        }
      }
    }
    persist()
  } catch { /* non-blocking */ }
}

/**
 * Mark a provider as connected (called after OAuth callback redirect returns).
 * The backend has already stored the tokens — we just update local state.
 */
function markConnected(provider: keyof OAuthState) {
  oauthState.value[provider] = {
    connected: true,
    lastSync: new Date().toISOString(),
  }
  persist()
}

/**
 * Redirect the browser to the backend Spotify OAuth flow.
 * The JWT is passed as a query param since browser redirects can't set headers.
 */
function connectSpotify() {
  const { token } = useAuthStore()
  if (!token.value) return
  window.location.href = `${API}/api/spotify/connect?token=${token.value}`
}

/**
 * Fetch the 3 nearest psychological neighbors from Pinecone via the backend.
 */
async function fetchMatches() {
  const { apiFetch } = useAuthStore()
  matchesLoading.value = true
  matchesError.value = null
  try {
    matches.value = await apiFetch<VibeMatch[]>('/api/intake/match')
  } catch (e: any) {
    matchesError.value = e.message
  } finally {
    matchesLoading.value = false
  }
}

/**
 * Fetch the user's Oracle coordinate (if synthesized).
 */
async function fetchOracleCoordinate() {
  const { apiFetch } = useAuthStore()
  try {
    oracleCoordinate.value = await apiFetch<OracleCoordinate>('/api/oracle/coordinate')
  } catch { /* non-blocking */ }
}

/**
 * Trigger Oracle synthesis — sends all connected provider flags to the backend,
 * which kicks off the LLM psychological coordinate pipeline as a background task.
 */
async function triggerSynthesis() {
  const { apiFetch } = useAuthStore()
  const providers = ['spotify', 'twitter', 'google', 'strava', 'costar', 'letterboxd', 'steam'] as const
  const payload: Record<string, { data: Record<string, unknown> }> = {}

  for (const p of providers) {
    payload[p === 'google' ? 'gcal' : p] = {
      data: oauthState.value[p].connected
        ? { connected: true, synced_at: oauthState.value[p].lastSync }
        : {},
    }
  }

  return apiFetch<{ status: string; message: string }>('/api/oracle/synthesize', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

/**
 * Send an accept or reject action for a matched user.
 * Returns the interaction result including mutual match status.
 */
async function interactWithMatch(targetId: string, action: 'accept' | 'reject'): Promise<InteractResult> {
  const { apiFetch } = useAuthStore()
  const result = await apiFetch<InteractResult>('/api/match/interact', {
    method: 'POST',
    body: JSON.stringify({ target_id: targetId, action }),
  })

  // Update local match state
  const match = matches.value.find((m) => m.user_id === targetId)
  if (match) {
    ;(match as VibeMatch).my_action = action
  }

  if (result.mutual_match) {
    mutualMatchUserId.value = targetId
  }

  return result
}

function clearMutualMatch() {
  mutualMatchUserId.value = null
}

function disconnectAll() {
  oauthState.value = defaultOAuthState()
  matches.value = []
  localStorage.removeItem(OAUTH_KEY)
}

// ── Export ───────────────────────────────────────────────────────────────────

export function useVibeStore() {
  return {
    oauthState: readonly(oauthState),
    matches: readonly(matches),
    matchesLoading: readonly(matchesLoading),
    matchesError: readonly(matchesError),
    isMatchReady,

    mutualMatchUserId: readonly(mutualMatchUserId),
    oracleCoordinate: readonly(oracleCoordinate),

    markConnected,
    syncConnectors,
    fetchOracleCoordinate,
    connectSpotify,
    triggerSynthesis,
    fetchMatches,
    interactWithMatch,
    clearMutualMatch,
    disconnectAll,
  }
}
