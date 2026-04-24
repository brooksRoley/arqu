import { ref, readonly } from 'vue'
import { useAuthStore } from './useAuthStore'
import type { RevealData, FittingData } from './useVibeStore'

const revealData = ref<RevealData | null>(null)
const revealLoading = ref(false)
const revealError = ref<string | null>(null)

async function fetchReveal(matchId: string) {
  const { apiFetch } = useAuthStore()
  revealLoading.value = true
  revealError.value = null
  try {
    revealData.value = await apiFetch<RevealData>(`/api/match/reveal/${matchId}`)
  } catch (e: any) {
    revealError.value = e.message
  } finally {
    revealLoading.value = false
  }
}

async function saveFitting(phase: 'self' | 'ideal', data: FittingData) {
  const { apiFetch } = useAuthStore()
  await apiFetch('/api/intake/fitting', {
    method: 'POST',
    body: JSON.stringify({ phase, data }),
  })
}

function hasFittingData(): { self: boolean; ideal: boolean } {
  return {
    self: revealData.value?.self?.fitting_self != null,
    ideal: revealData.value?.self?.fitting_ideal != null,
  }
}

export function useRevealStore() {
  return {
    revealData: readonly(revealData),
    revealLoading: readonly(revealLoading),
    revealError: readonly(revealError),
    fetchReveal,
    saveFitting,
    hasFittingData,
  }
}
