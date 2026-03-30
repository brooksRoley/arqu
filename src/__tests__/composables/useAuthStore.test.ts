import { describe, it, expect, vi, beforeEach } from 'vitest'

// Re-import the module fresh for each test so singleton state is clean.
// vitest resets modules between each describe block if configured, but we
// use dynamic imports inside a factory to avoid cross-test contamination.

function mockFetchOk(body: unknown, status = 200) {
  return vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
    ok: status < 400,
    status,
    json: () => Promise.resolve(body),
    statusText: status === 200 ? 'OK' : 'Error',
  }))
}

function mockFetchError(status: number, detail = 'Unauthorized') {
  return vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
    ok: false,
    status,
    json: () => Promise.resolve({ detail }),
    statusText: 'Error',
  }))
}

describe('useAuthStore', () => {
  // Get a fresh module instance per test to avoid singleton bleed.
  async function getStore() {
    vi.resetModules()
    const { useAuthStore } = await import('@/composables/useAuthStore')
    return useAuthStore()
  }

  describe('authHeaders', () => {
    it('returns empty object when no token is stored', async () => {
      const { authHeaders } = await getStore()
      expect(authHeaders()).toEqual({})
    })

    it('returns Authorization header when token is in localStorage', async () => {
      localStorage.setItem('channelzero-jwt', 'test-token')
      const { authHeaders } = await getStore()
      expect(authHeaders()).toEqual({ Authorization: 'Bearer test-token' })
    })
  })

  describe('login', () => {
    it('stores token and fetches user on success', async () => {
      const { login, token, user } = await getStore()

      mockFetchOk({ access_token: 'tok-abc' })
      // Second fetch for /api/auth/me
      const fetchMock = vi.fn()
        .mockResolvedValueOnce({ ok: true, status: 200, json: () => Promise.resolve({ access_token: 'tok-abc' }) })
        .mockResolvedValueOnce({ ok: true, status: 200, json: () => Promise.resolve({ id: 'u1', email: 'a@b.com', display_name: 'Alice', created_at: '2024-01-01' }) })
      vi.stubGlobal('fetch', fetchMock)

      await login('a@b.com', 'pw')

      expect(token.value).toBe('tok-abc')
      expect(localStorage.getItem('channelzero-jwt')).toBe('tok-abc')
      expect(user.value?.email).toBe('a@b.com')
    })

    it('sets error and rethrows on API failure', async () => {
      const { login, error } = await getStore()
      mockFetchError(401, 'Invalid credentials')

      await expect(login('bad@b.com', 'wrong')).rejects.toThrow('Invalid credentials')
      expect(error.value).toBe('Invalid credentials')
    })

    it('sends correct POST body', async () => {
      const { login } = await getStore()
      const fetchMock = vi.fn()
        .mockResolvedValueOnce({ ok: true, status: 200, json: () => Promise.resolve({ access_token: 't' }) })
        .mockResolvedValueOnce({ ok: true, status: 200, json: () => Promise.resolve({ id: 'u1', email: 'a@b.com', display_name: null, created_at: '' }) })
      vi.stubGlobal('fetch', fetchMock)

      await login('a@b.com', 'secret')

      const [url, opts] = fetchMock.mock.calls[0]
      expect(url).toContain('/api/auth/login')
      expect(JSON.parse(opts.body)).toEqual({ email: 'a@b.com', password: 'secret' })
    })
  })

  describe('loginWithProvider', () => {
    it('calls /api/auth/google with just code for Google', async () => {
      const { loginWithProvider } = await getStore()
      const fetchMock = vi.fn().mockResolvedValue({
        ok: true, status: 200,
        json: () => Promise.resolve({
          access_token: 'g-tok',
          user: { id: 'g1', email: 'g@google.com', display_name: 'G User', created_at: '' },
        }),
      })
      vi.stubGlobal('fetch', fetchMock)

      await loginWithProvider('google', 'auth-code-xyz')

      const [url, opts] = fetchMock.mock.calls[0]
      expect(url).toContain('/api/auth/google')
      expect(JSON.parse(opts.body)).toEqual({ code: 'auth-code-xyz' })
    })

    it('includes code_verifier in POST body for X/PKCE', async () => {
      const { loginWithProvider } = await getStore()
      const fetchMock = vi.fn().mockResolvedValue({
        ok: true, status: 200,
        json: () => Promise.resolve({
          access_token: 'x-tok',
          user: { id: 'x1', email: null, display_name: 'X User', created_at: '' },
        }),
      })
      vi.stubGlobal('fetch', fetchMock)

      await loginWithProvider('x', 'x-code', 'pkce-verifier-abc')

      const [url, opts] = fetchMock.mock.calls[0]
      expect(url).toContain('/api/auth/x')
      const body = JSON.parse(opts.body)
      expect(body.code).toBe('x-code')
      expect(body.code_verifier).toBe('pkce-verifier-abc')
    })

    it('stores token and user on success', async () => {
      const { loginWithProvider, token, user } = await getStore()
      vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
        ok: true, status: 200,
        json: () => Promise.resolve({
          access_token: 'prov-tok',
          user: { id: 'p1', email: 'p@x.com', display_name: 'PUser', created_at: '2024-01-01' },
        }),
      }))

      await loginWithProvider('google', 'code')

      expect(token.value).toBe('prov-tok')
      expect(localStorage.getItem('channelzero-jwt')).toBe('prov-tok')
      expect(user.value?.id).toBe('p1')
      expect(JSON.parse(localStorage.getItem('channelzero-user')!).id).toBe('p1')
    })

    it('throws and sets error on API failure', async () => {
      const { loginWithProvider, error } = await getStore()
      mockFetchError(400, 'Invalid code')

      await expect(loginWithProvider('google', 'bad-code')).rejects.toThrow('Invalid code')
      expect(error.value).toBe('Invalid code')
    })
  })

  describe('fetchMe', () => {
    it('updates user from /api/auth/me', async () => {
      // Token must be seeded BEFORE getStore() since the module reads it at init time
      localStorage.setItem('channelzero-jwt', 'valid-token')
      const { fetchMe, user } = await getStore()
      vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
        ok: true, status: 200,
        json: () => Promise.resolve({ id: 'me1', email: 'me@c.com', display_name: 'Me', created_at: '' }),
      }))

      await fetchMe()

      expect(user.value?.email).toBe('me@c.com')
    })

    it('calls logout when /api/auth/me returns 401', async () => {
      localStorage.setItem('channelzero-jwt', 'expired-token')
      const store = await getStore()
      vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
        ok: false, status: 401,
        json: () => Promise.resolve({ detail: 'Expired' }),
      }))

      await store.fetchMe()

      expect(store.token.value).toBeNull()
      expect(localStorage.getItem('channelzero-jwt')).toBeNull()
    })

    it('does nothing when no token is present', async () => {
      // No token in localStorage → module initializes with token=null
      const { fetchMe } = await getStore()
      const fetchMock = vi.fn()
      vi.stubGlobal('fetch', fetchMock)

      await fetchMe()

      expect(fetchMock).not.toHaveBeenCalled()
    })
  })

  describe('logout', () => {
    it('clears token, user, and localStorage', async () => {
      localStorage.setItem('channelzero-jwt', 'tok')
      localStorage.setItem('channelzero-user', JSON.stringify({ id: 'u1' }))
      const { logout, token, user } = await getStore()

      logout()

      expect(token.value).toBeNull()
      expect(user.value).toBeNull()
      expect(localStorage.getItem('channelzero-jwt')).toBeNull()
      expect(localStorage.getItem('channelzero-user')).toBeNull()
    })
  })
})
