import { ref } from 'vue'

export interface ConnectorAvailability {
  providers: Record<string, boolean>
  llm: boolean
}

const API = (import.meta as any).env?.VITE_API_URL || ''

const availability = ref<ConnectorAvailability | null>(null)
const loading = ref(false)
let inflight: Promise<ConnectorAvailability | null> | null = null

async function fetchAvailability(): Promise<ConnectorAvailability | null> {
  if (availability.value) return availability.value
  if (inflight) return inflight

  loading.value = true
  inflight = (async () => {
    try {
      const resp = await fetch(`${API}/api/connectors/available`)
      if (!resp.ok) return null
      const data = (await resp.json()) as ConnectorAvailability
      availability.value = data
      return data
    } catch {
      return null
    } finally {
      loading.value = false
      inflight = null
    }
  })()
  return inflight
}

function isAvailable(provider: string): boolean {
  // Default to true while we're still fetching — avoid flash-of-disabled-buttons.
  // Once data is in, only providers explicitly marked false are blocked.
  if (!availability.value) return true
  return availability.value.providers[provider] !== false
}

export function useConnectorAvailability() {
  return {
    availability,
    loading,
    fetchAvailability,
    isAvailable,
  }
}
