import { useAuthStore } from './useAuthStore'

// ── Types ──────────────────────────────────────────────────────────

export interface StreakData {
  streak: number
  today_active: boolean
  last_7_days: { date: string; active: boolean }[]
}

// ── Composable ─────────────────────────────────────────────────────

/**
 * Lightweight wrapper around the analytics funnel endpoints.
 *
 * `logEvent` is fire-and-forget: it never throws, never blocks the UI, and
 * is a no-op when the user isn't authenticated (so public routes like
 * /zeromind don't trigger a 401 → forced logout).
 */
export function useAnalytics() {
  const { apiFetch, isAuthenticated } = useAuthStore()

  function logEvent(event: string, metadata: Record<string, unknown> = {}) {
    if (!isAuthenticated.value) return
    apiFetch('/api/analytics/event', {
      method: 'POST',
      body: JSON.stringify({ event, metadata }),
    }).catch(() => { /* analytics must never break the experience */ })
  }

  async function fetchStreak(): Promise<StreakData | null> {
    if (!isAuthenticated.value) return null
    try {
      return await apiFetch<StreakData>('/api/analytics/streak')
    } catch {
      return null
    }
  }

  return { logEvent, fetchStreak }
}
