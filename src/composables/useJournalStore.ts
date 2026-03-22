import { ref, computed } from 'vue'
import { usePollStore } from './usePollStore'
import type { PollToken } from './usePollStore'

// ── Types ──────────────────────────────────────────────────────────

export interface JournalDrawing {
  dataUrl: string        // canvas toDataURL() png
  createdAt: number
}

export interface JournalAudioClip {
  blob: Blob | null      // in-memory only (not persisted to localStorage)
  duration: number        // seconds
  createdAt: number
}

export interface JournalEntry {
  id: string
  text: string
  drawings: JournalDrawing[]
  audioClips: JournalAudioClip[]
  mood: string | null     // optional freeform tag
  pollToken: PollToken | null
  createdAt: number
  updatedAt: number
}

export interface JournalSynthesis {
  entryIds: string[]
  summary: string
  keywords: string[]
  generatedAt: number
}

// ── Storage ────────────────────────────────────────────────────────

const STORAGE_KEY = 'channelzero-journal'

function generateId(): string {
  return `j-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

function loadEntries(): JournalEntry[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw) as JournalEntry[]
    // Audio blobs can't be serialised — null them out on hydration
    return parsed.map((e) => ({
      ...e,
      audioClips: e.audioClips.map((c) => ({ ...c, blob: null }))
    }))
  } catch {
    return []
  }
}

function persistEntries(entries: JournalEntry[]) {
  // Strip audio blobs before serialisation
  const serialisable = entries.map((e) => ({
    ...e,
    audioClips: e.audioClips.map((c) => ({ ...c, blob: null }))
  }))
  localStorage.setItem(STORAGE_KEY, JSON.stringify(serialisable))
}

// ── Module-level singleton state ───────────────────────────────────

const entries = ref<JournalEntry[]>(loadEntries())
const activeEntryId = ref<string | null>(null)
const syntheses = ref<JournalSynthesis[]>([])

// ── Derived ────────────────────────────────────────────────────────

const activeEntry = computed(() =>
  entries.value.find((e) => e.id === activeEntryId.value) ?? null
)

const todayEntries = computed(() => {
  const start = new Date()
  start.setHours(0, 0, 0, 0)
  const startMs = start.getTime()
  return entries.value.filter((e) => e.createdAt >= startMs)
})

const sortedEntries = computed(() =>
  [...entries.value].sort((a, b) => b.createdAt - a.createdAt)
)

// ── Actions ────────────────────────────────────────────────────────

function createEntry(initialText = ''): JournalEntry {
  const { token } = usePollStore()
  const entry: JournalEntry = {
    id: generateId(),
    text: initialText,
    drawings: [],
    audioClips: [],
    mood: null,
    pollToken: token.value ? { ...token.value } : null,
    createdAt: Date.now(),
    updatedAt: Date.now()
  }
  entries.value.unshift(entry)
  activeEntryId.value = entry.id
  persistEntries(entries.value)
  return entry
}

function updateEntryText(id: string, text: string) {
  const entry = entries.value.find((e) => e.id === id)
  if (!entry) return
  entry.text = text
  entry.updatedAt = Date.now()
  persistEntries(entries.value)
}

function setMood(id: string, mood: string | null) {
  const entry = entries.value.find((e) => e.id === id)
  if (!entry) return
  entry.mood = mood
  entry.updatedAt = Date.now()
  persistEntries(entries.value)
}

function addDrawing(id: string, dataUrl: string) {
  const entry = entries.value.find((e) => e.id === id)
  if (!entry) return
  entry.drawings.push({ dataUrl, createdAt: Date.now() })
  entry.updatedAt = Date.now()
  persistEntries(entries.value)
}

function removeDrawing(entryId: string, drawingIndex: number) {
  const entry = entries.value.find((e) => e.id === entryId)
  if (!entry) return
  entry.drawings.splice(drawingIndex, 1)
  entry.updatedAt = Date.now()
  persistEntries(entries.value)
}

function addAudioClip(id: string, blob: Blob, duration: number) {
  const entry = entries.value.find((e) => e.id === id)
  if (!entry) return
  entry.audioClips.push({ blob, duration, createdAt: Date.now() })
  entry.updatedAt = Date.now()
  // Audio blobs can't be persisted to localStorage — metadata only
  persistEntries(entries.value)
}

function deleteEntry(id: string) {
  const idx = entries.value.findIndex((e) => e.id === id)
  if (idx === -1) return
  entries.value.splice(idx, 1)
  if (activeEntryId.value === id) {
    activeEntryId.value = entries.value[0]?.id ?? null
  }
  persistEntries(entries.value)
}

function setActiveEntry(id: string | null) {
  activeEntryId.value = id
}

// ── Synthesis ──────────────────────────────────────────────────────
// Produces a summary of today's entries for the daily check-in view.
// In phase 2, this can call an LLM API for real synthesis.

function synthesizeToday(): JournalSynthesis {
  const today = todayEntries.value
  const allText = today.map((e) => e.text).filter(Boolean).join('\n\n')
  const allMoods = today.map((e) => e.mood).filter(Boolean) as string[]

  // Naive keyword extraction: most common words > 4 chars
  const wordCounts = new Map<string, number>()
  allText
    .toLowerCase()
    .split(/\W+/)
    .filter((w) => w.length > 4)
    .forEach((w) => wordCounts.set(w, (wordCounts.get(w) || 0) + 1))

  const keywords = [...wordCounts.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)
    .map(([word]) => word)

  const synthesis: JournalSynthesis = {
    entryIds: today.map((e) => e.id),
    summary: allText.slice(0, 500) + (allText.length > 500 ? '...' : ''),
    keywords: [...new Set([...allMoods, ...keywords])],
    generatedAt: Date.now()
  }

  syntheses.value.push(synthesis)
  return synthesis
}

// ── Collect all text for feeding into the story store ───────────

function getEntryTextForStoryStore(id: string): string {
  const entry = entries.value.find((e) => e.id === id)
  return entry?.text ?? ''
}

function getAllTodayText(): string {
  return todayEntries.value.map((e) => e.text).filter(Boolean).join('\n\n')
}

// ── Export ──────────────────────────────────────────────────────────

export function useJournalStore() {
  return {
    // State
    entries,
    activeEntryId,
    activeEntry,
    todayEntries,
    sortedEntries,
    syntheses,

    // Entry CRUD
    createEntry,
    updateEntryText,
    setMood,
    addDrawing,
    removeDrawing,
    addAudioClip,
    deleteEntry,
    setActiveEntry,

    // Synthesis
    synthesizeToday,

    // Story store bridge
    getEntryTextForStoryStore,
    getAllTodayText,
  }
}
