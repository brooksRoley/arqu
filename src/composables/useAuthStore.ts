import { ref, computed, readonly } from 'vue'

// ── Types ──────────────────────────────────────────────────────────

export interface User {
  id: string
  email: string
  display_name: string | null
  created_at: string
}

export interface AuthState {
  token: string | null
  user: User | null
}

// ── Storage ────────────────────────────────────────────────────────

const TOKEN_KEY = 'channelzero-jwt'
const USER_KEY = 'channelzero-user'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// ── Module-level singleton state ───────────────────────────────────

const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))
const user = ref<User | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

// Hydrate user from localStorage
try {
  const stored = localStorage.getItem(USER_KEY)
  if (stored) user.value = JSON.parse(stored)
} catch { /* ignore */ }

// ── Derived ────────────────────────────────────────────────────────

const isAuthenticated = computed(() => !!token.value)

// ── Helpers ────────────────────────────────────────────────────────

function authHeaders(): Record<string, string> {
  if (!token.value) return {}
  return { Authorization: `Bearer ${token.value}` }
}

async function apiFetch<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    ...opts,
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
      ...(opts.headers || {}),
    },
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(body.detail || `Request failed: ${res.status}`)
  }
  return res.json()
}

// ── Actions ────────────────────────────────────────────────────────

async function register(email: string, password: string, displayName?: string) {
  loading.value = true
  error.value = null
  try {
    const data = await apiFetch<{ access_token: string }>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, display_name: displayName || null }),
    })
    token.value = data.access_token
    localStorage.setItem(TOKEN_KEY, data.access_token)
    await fetchMe()
  } catch (e: any) {
    error.value = e.message
    throw e
  } finally {
    loading.value = false
  }
}

async function login(email: string, password: string) {
  loading.value = true
  error.value = null
  try {
    const data = await apiFetch<{ access_token: string }>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
    token.value = data.access_token
    localStorage.setItem(TOKEN_KEY, data.access_token)
    await fetchMe()
  } catch (e: any) {
    error.value = e.message
    throw e
  } finally {
    loading.value = false
  }
}

async function fetchMe() {
  if (!token.value) return
  try {
    const data = await apiFetch<User>('/api/auth/me')
    user.value = data
    localStorage.setItem(USER_KEY, JSON.stringify(data))
  } catch {
    // Token expired or invalid — clear state
    logout()
  }
}

function logout() {
  token.value = null
  user.value = null
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

// ── Export ──────────────────────────────────────────────────────────

export function useAuthStore() {
  return {
    token: readonly(token),
    user: readonly(user),
    loading: readonly(loading),
    error: readonly(error),
    isAuthenticated,

    register,
    login,
    logout,
    fetchMe,

    // Expose for other composables that need authenticated fetch
    authHeaders,
    apiFetch,
  }
}
