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
}

export interface VibeMatch {
  user_id: string
  display_name: string
  attachment_style: string | null
  defense_mechanism: string | null
  similarity: number
}

// ── Storage key ──────────────────────────────────────────────────────────────

const OAUTH_KEY = 'channelzero-oauth'
const API = import.meta.env.VITE_API_URL || ''

// ── Module-level singleton state ─────────────────────────────────────────────

function defaultOAuthState(): OAuthState {
  return {
    spotify: { connected: false, lastSync: null },
    twitter: { connected: false, lastSync: null },
    google:  { connected: false, lastSync: null },
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

// ── Derived ──────────────────────────────────────────────────────────────────

const isMatchReady = computed(() => oauthState.value.spotify.connected)

// ── Helpers ──────────────────────────────────────────────────────────────────

function persist() {
  localStorage.setItem(OAUTH_KEY, JSON.stringify(oauthState.value))
}

// ── Actions ──────────────────────────────────────────────────────────────────

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

    markConnected,
    connectSpotify,
    fetchMatches,
    disconnectAll,
  }
}
