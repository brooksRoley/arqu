import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import GoogleCallback from '@/views/GoogleCallback.vue'

// ── Top-level mutable mock state ──────────────────────────────────
// vitest hoists vi.mock calls so we can't define them inside helpers.
// Instead we hold mutable refs and update them per-test.

const mockQuery: Record<string, string> = {}
const mockReplace = vi.fn()
const mockLoginWithProvider = vi.fn()

vi.mock('vue-router', () => ({
  useRoute:  () => ({ query: mockQuery }),
  useRouter: () => ({ replace: mockReplace }),
}))

vi.mock('@/composables/useAuthStore', () => ({
  useAuthStore: () => ({ loginWithProvider: mockLoginWithProvider }),
}))

// ── Helpers ────────────────────────────────────────────────────────

function setQuery(q: Record<string, string>) {
  // Clear all keys and set new ones on the shared object.
  Object.keys(mockQuery).forEach(k => delete mockQuery[k])
  Object.assign(mockQuery, q)
}

async function mountCallback() {
  const wrapper = mount(GoogleCallback)
  await flushPromises()
  return wrapper
}

// ── Tests ──────────────────────────────────────────────────────────

describe('GoogleCallback', () => {
  beforeEach(() => {
    mockReplace.mockReset()
    mockLoginWithProvider.mockReset()
    setQuery({})
  })

  it('calls loginWithProvider("google", code) when code query param is present', async () => {
    mockLoginWithProvider.mockResolvedValue(undefined)
    setQuery({ code: 'google-auth-code-abc' })
    await mountCallback()

    expect(mockLoginWithProvider).toHaveBeenCalledOnce()
    expect(mockLoginWithProvider).toHaveBeenCalledWith('google', 'google-auth-code-abc')
  })

  it('does not pass a code_verifier — Google uses server-side exchange, not PKCE', async () => {
    mockLoginWithProvider.mockResolvedValue(undefined)
    setQuery({ code: 'google-code' })
    await mountCallback()

    const call = mockLoginWithProvider.mock.calls[0]
    // Third argument (codeVerifier) must be absent or undefined
    expect(call[2]).toBeUndefined()
  })

  it('redirects to /calibrate after successful login', async () => {
    mockLoginWithProvider.mockResolvedValue(undefined)
    setQuery({ code: 'valid-code' })
    await mountCallback()

    expect(mockReplace).toHaveBeenCalledWith('/calibrate')
  })

  it('shows "Missing authorization code" and skips login when code is absent', async () => {
    setQuery({})
    const wrapper = await mountCallback()

    expect(mockLoginWithProvider).not.toHaveBeenCalled()
    expect(mockReplace).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('Missing authorization code')
  })

  it('does not redirect when loginWithProvider throws', async () => {
    mockLoginWithProvider.mockRejectedValue(new Error('Token exchange failed'))
    setQuery({ code: 'bad-code' })
    await mountCallback()

    expect(mockReplace).not.toHaveBeenCalled()
  })

  it('displays the error message returned by loginWithProvider', async () => {
    mockLoginWithProvider.mockRejectedValue(new Error('Google sign-in rejected'))
    setQuery({ code: 'bad-code' })
    const wrapper = await mountCallback()

    expect(wrapper.text()).toContain('Google sign-in rejected')
  })

  it('shows a fallback error when the thrown error has no message', async () => {
    mockLoginWithProvider.mockRejectedValue(new Error())
    setQuery({ code: 'code' })
    const wrapper = await mountCallback()

    expect(wrapper.text()).toContain('Google sign-in failed')
  })
})
