import { describe, it, expect, vi, beforeEach } from 'vitest'

// Helper: stub fetch to return a successful response
function mockFetchOk(body: unknown) {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
    ok: true, status: 200,
    json: () => Promise.resolve(body),
  }))
}

function mockFetchError(status: number, detail = 'Error') {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
    ok: false, status,
    json: () => Promise.resolve({ detail }),
  }))
}

// Get fresh module instances so singleton refs reset between tests.
async function getStores() {
  vi.resetModules()

  // Provide a token so authStore.apiFetch sends the header
  localStorage.setItem('channelzero-jwt', 'test-jwt')

  const { useVibeStore } = await import('@/composables/useVibeStore')
  return { vibeStore: useVibeStore() }
}

describe('useVibeStore', () => {
  describe('markConnected', () => {
    it('sets connected=true and a valid ISO lastSync for the provider', async () => {
      const { vibeStore } = await getStores()
      vibeStore.markConnected('spotify')

      expect(vibeStore.oauthState.value.spotify.connected).toBe(true)
      expect(vibeStore.oauthState.value.spotify.lastSync).toMatch(
        /^\d{4}-\d{2}-\d{2}T/  // ISO 8601
      )
    })

    it('persists connection state to localStorage', async () => {
      const { vibeStore } = await getStores()
      vibeStore.markConnected('strava')

      const stored = JSON.parse(localStorage.getItem('channelzero-oauth')!)
      expect(stored.strava.connected).toBe(true)
    })

    it('marks each provider independently without affecting others', async () => {
      const { vibeStore } = await getStores()
      vibeStore.markConnected('twitter')

      expect(vibeStore.oauthState.value.twitter.connected).toBe(true)
      expect(vibeStore.oauthState.value.spotify.connected).toBe(false)
      expect(vibeStore.oauthState.value.strava.connected).toBe(false)
    })

    it('supports all declared providers', async () => {
      const { vibeStore } = await getStores()
      const providers = ['spotify', 'twitter', 'google', 'strava', 'costar', 'letterboxd', 'steam'] as const

      for (const p of providers) {
        vibeStore.markConnected(p)
        expect(vibeStore.oauthState.value[p].connected).toBe(true)
      }
    })
  })

  describe('fetchMatches', () => {
    it('calls /api/intake/match and stores results', async () => {
      const { vibeStore } = await getStores()
      const mockMatches = [
        { user_id: 'u1', display_name: 'Alice', attachment_style: 'Secure', defense_mechanism: null, similarity: 0.95 },
        { user_id: 'u2', display_name: 'Bob',   attachment_style: 'Anxious', defense_mechanism: 'Projection', similarity: 0.88 },
      ]
      mockFetchOk(mockMatches)

      await vibeStore.fetchMatches()

      expect(vibeStore.matches.value).toHaveLength(2)
      expect(vibeStore.matches.value[0].user_id).toBe('u1')
      expect(vibeStore.matches.value[0].similarity).toBe(0.95)
    })

    it('sets matchesError and leaves matches empty on failure', async () => {
      const { vibeStore } = await getStores()
      mockFetchError(500, 'Pinecone unavailable')

      await vibeStore.fetchMatches()

      expect(vibeStore.matches.value).toHaveLength(0)
      expect(vibeStore.matchesError.value).toBe('Pinecone unavailable')
    })

    it('sets matchesLoading false after resolution', async () => {
      const { vibeStore } = await getStores()
      mockFetchOk([])

      await vibeStore.fetchMatches()

      expect(vibeStore.matchesLoading.value).toBe(false)
    })
  })

  describe('triggerSynthesis', () => {
    it('includes connected providers with synced_at in the payload', async () => {
      const { vibeStore } = await getStores()
      vibeStore.markConnected('spotify')
      vibeStore.markConnected('strava')
      const fetchMock = vi.fn().mockResolvedValue({
        ok: true, status: 200,
        json: () => Promise.resolve({ status: 'queued', message: 'ok' }),
      })
      vi.stubGlobal('fetch', fetchMock)

      await vibeStore.triggerSynthesis()

      const [url, opts] = fetchMock.mock.calls[0]
      expect(url).toContain('/api/oracle/synthesize')
      const payload = JSON.parse(opts.body)
      expect(payload.spotify.data.connected).toBe(true)
      expect(payload.strava.data.connected).toBe(true)
      expect(payload.spotify.data.synced_at).toBeTruthy()
    })

    it('sends empty data objects for disconnected providers', async () => {
      const { vibeStore } = await getStores()
      const fetchMock = vi.fn().mockResolvedValue({
        ok: true, status: 200,
        json: () => Promise.resolve({ status: 'queued', message: 'ok' }),
      })
      vi.stubGlobal('fetch', fetchMock)

      await vibeStore.triggerSynthesis()

      const payload = JSON.parse(fetchMock.mock.calls[0][1].body)
      // All providers start disconnected — should send empty objects
      expect(payload.spotify.data).toEqual({})
      expect(payload.twitter.data).toEqual({})
    })

    it('maps google provider key to gcal in the payload', async () => {
      const { vibeStore } = await getStores()
      vibeStore.markConnected('google')
      const fetchMock = vi.fn().mockResolvedValue({
        ok: true, status: 200,
        json: () => Promise.resolve({ status: 'queued', message: 'ok' }),
      })
      vi.stubGlobal('fetch', fetchMock)

      await vibeStore.triggerSynthesis()

      const payload = JSON.parse(fetchMock.mock.calls[0][1].body)
      // The backend expects 'gcal', not 'google'
      expect(payload.gcal).toBeDefined()
      expect(payload.gcal.data.connected).toBe(true)
      expect(payload.google).toBeUndefined()
    })
  })

  describe('disconnectAll', () => {
    it('resets all providers to disconnected and clears localStorage', async () => {
      const { vibeStore } = await getStores()
      vibeStore.markConnected('spotify')
      vibeStore.markConnected('strava')

      vibeStore.disconnectAll()

      expect(vibeStore.oauthState.value.spotify.connected).toBe(false)
      expect(vibeStore.oauthState.value.strava.connected).toBe(false)
      expect(localStorage.getItem('channelzero-oauth')).toBeNull()
    })

    it('clears matches array', async () => {
      const { vibeStore } = await getStores()
      mockFetchOk([{ user_id: 'u1', display_name: 'A', attachment_style: null, defense_mechanism: null, similarity: 0.9 }])
      await vibeStore.fetchMatches()

      vibeStore.disconnectAll()

      expect(vibeStore.matches.value).toHaveLength(0)
    })
  })

  describe('isMatchReady', () => {
    it('is false when Spotify is not connected', async () => {
      const { vibeStore } = await getStores()
      expect(vibeStore.isMatchReady.value).toBe(false)
    })

    it('is true when Spotify is connected', async () => {
      const { vibeStore } = await getStores()
      vibeStore.markConnected('spotify')
      expect(vibeStore.isMatchReady.value).toBe(true)
    })
  })
})
