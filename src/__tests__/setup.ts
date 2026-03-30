// Global test setup — runs before every test file.
// Provides a fresh localStorage stub and a resettable fetch mock.

import { vi, beforeEach, afterEach } from 'vitest'

// ── localStorage stub ─────────────────────────────────────────────
// happy-dom ships a real localStorage but we want per-test isolation.
const store: Record<string, string> = {}

vi.stubGlobal('localStorage', {
  getItem:    (k: string) => store[k] ?? null,
  setItem:    (k: string, v: string) => { store[k] = v },
  removeItem: (k: string) => { delete store[k] },
  clear:      () => { for (const k in store) delete store[k] },
  get length() { return Object.keys(store).length },
  key: (i: number) => Object.keys(store)[i] ?? null,
})

beforeEach(() => {
  localStorage.clear()
})
