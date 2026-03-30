import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import XCallback from '@/views/XCallback.vue'

const VERIFIER_KEY = 'channelzero-x-pkce-verifier'

// ── Top-level mutable mock state ──────────────────────────────────

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

function setQuery(q: Record<string, string>) {
  Object.keys(mockQuery).forEach(k => delete mockQuery[k])
  Object.assign(mockQuery, q)
}

async function mountCallback() {
  const wrapper = mount(XCallback)
  await flushPromises()
  return wrapper
}

// ── Tests ──────────────────────────────────────────────────────────

describe('XCallback', () => {
  beforeEach(() => {
    mockReplace.mockReset()
    mockLoginWithProvider.mockReset()
    setQuery({})
  })

  it('calls loginWithProvider("x", code, verifier) with all three arguments', async () => {
    mockLoginWithProvider.mockResolvedValue(undefined)
    localStorage.setItem(VERIFIER_KEY, 'pkce-verifier-xyz')
    setQuery({ code: 'x-auth-code' })
    await mountCallback()

    expect(mockLoginWithProvider).toHaveBeenCalledOnce()
    expect(mockLoginWithProvider).toHaveBeenCalledWith('x', 'x-auth-code', 'pkce-verifier-xyz')
  })

  it('redirects to /calibrate on successful login', async () => {
    mockLoginWithProvider.mockResolvedValue(undefined)
    localStorage.setItem(VERIFIER_KEY, 'v')
    setQuery({ code: 'x-code' })
    await mountCallback()

    expect(mockReplace).toHaveBeenCalledWith('/calibrate')
  })

  it('removes the PKCE verifier from localStorage after successful login', async () => {
    mockLoginWithProvider.mockResolvedValue(undefined)
    localStorage.setItem(VERIFIER_KEY, 'secret-verifier')
    setQuery({ code: 'x-code' })
    await mountCallback()

    expect(localStorage.getItem(VERIFIER_KEY)).toBeNull()
  })

  it('shows "Missing authorization code" and skips login when code is absent', async () => {
    localStorage.setItem(VERIFIER_KEY, 'v')
    setQuery({})
    const wrapper = await mountCallback()

    expect(mockLoginWithProvider).not.toHaveBeenCalled()
    expect(mockReplace).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('Missing authorization code')
  })

  it('shows "PKCE verifier" error and skips login when verifier is absent from localStorage', async () => {
    // No verifier set in localStorage
    setQuery({ code: 'x-code' })
    const wrapper = await mountCallback()

    expect(mockLoginWithProvider).not.toHaveBeenCalled()
    expect(mockReplace).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('PKCE verifier')
  })

  it('preserves the PKCE verifier when code is absent (allows the user to retry)', async () => {
    localStorage.setItem(VERIFIER_KEY, 'safe-verifier')
    setQuery({})
    await mountCallback()

    expect(localStorage.getItem(VERIFIER_KEY)).toBe('safe-verifier')
  })

  it('does not redirect when loginWithProvider throws', async () => {
    mockLoginWithProvider.mockRejectedValue(new Error('X auth failed'))
    localStorage.setItem(VERIFIER_KEY, 'v')
    setQuery({ code: 'bad-code' })
    await mountCallback()

    expect(mockReplace).not.toHaveBeenCalled()
  })

  it('displays the error thrown by loginWithProvider', async () => {
    mockLoginWithProvider.mockRejectedValue(new Error('Rate limited'))
    localStorage.setItem(VERIFIER_KEY, 'v')
    setQuery({ code: 'x-code' })
    const wrapper = await mountCallback()

    expect(wrapper.text()).toContain('Rate limited')
  })

  it('passes code_verifier as the third positional argument (not nested in an object)', async () => {
    mockLoginWithProvider.mockResolvedValue(undefined)
    localStorage.setItem(VERIFIER_KEY, 'v')
    setQuery({ code: 'c' })
    await mountCallback()

    const [provider, code, verifier] = mockLoginWithProvider.mock.calls[0]
    expect(provider).toBe('x')
    expect(code).toBe('c')
    expect(verifier).toBe('v')
  })
})
