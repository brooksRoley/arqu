import { ref, computed } from 'vue'

export type Q1Answer = 'vivid-dreamer' | 'balanced-escapist' | 'grounded-realist'
export type Q2Answer = 'frequent-dissociation' | 'occasional-detachment' | 'fully-present'
export type Q3Answer = 'creative-storyteller' | 'structured-play' | 'independent-explorer'
export type Q4Answer = 'blank-slate' | 'context-dependent' | 'thought-rich'

export type ProfileTheme = 'dreamlike' | 'electric' | 'void' | 'organic' | 'liminal'

export interface PollAnswers {
  q1: Q1Answer | null
  q2: Q2Answer | null
  q3: Q3Answer | null
  q4: Q4Answer | null
}

export interface ThemePalette {
  primary: string
  accent: string
  background: string
}

export interface PollToken {
  answers: PollAnswers
  theme: ProfileTheme
  palette: ThemePalette
  tone: string
  archetype: string
  keywords: string[]
  adlibPrompt: string
}

const STORAGE_KEY = 'channelzero-poll-token'

const answers = ref<PollAnswers>({ q1: null, q2: null, q3: null, q4: null })
const token = ref<PollToken | null>(null)

// Hydrate from localStorage
try {
  const stored = localStorage.getItem(STORAGE_KEY)
  if (stored) {
    const parsed = JSON.parse(stored) as PollToken
    token.value = parsed
    answers.value = parsed.answers
  }
} catch {
  // ignore malformed storage
}

const PALETTES: Record<ProfileTheme, ThemePalette> = {
  dreamlike: { primary: '#7c3aed', accent: '#a78bfa', background: '#0f0820' },
  electric:  { primary: '#6366f1', accent: '#38bdf8', background: '#030712' },
  void:      { primary: '#334155', accent: '#94a3b8', background: '#020617' },
  organic:   { primary: '#059669', accent: '#d97706', background: '#0a150f' },
  liminal:   { primary: '#0891b2', accent: '#e879f9', background: '#0c1021' },
}

const PROFILES: Record<ProfileTheme, { tone: string; archetype: string; keywords: string[] }> = {
  dreamlike: {
    tone: 'ethereal and introspective',
    archetype: 'the dreamer',
    keywords: ['dreamscape', 'phosphorescent', 'soft-focus', 'reverie', 'gossamer', 'liminal'],
  },
  electric: {
    tone: 'charged and vivid',
    archetype: 'the visionary',
    keywords: ['resonant', 'crystalline', 'percussive', 'kinetic', 'luminous', 'sharp-edged'],
  },
  void: {
    tone: 'sparse and atmospheric',
    archetype: 'the observer',
    keywords: ['static', 'hollow', 'whitespace', 'echo', 'dissolve', 'negative-space'],
  },
  organic: {
    tone: 'grounded and textured',
    archetype: 'the maker',
    keywords: ['tactile', 'rooted', 'seasonal', 'layered', 'tangible', 'worn'],
  },
  liminal: {
    tone: 'ambient and in-between',
    archetype: 'the wanderer',
    keywords: ['threshold', 'translucent', 'drifting', 'half-remembered', 'fog', 'between'],
  },
}

function deriveTheme(a: PollAnswers): ProfileTheme {
  if (!a.q1 || !a.q2 || !a.q3 || !a.q4) return 'liminal'

  const fantasyScore =
    ({ 'vivid-dreamer': 3, 'balanced-escapist': 2, 'grounded-realist': 1 } as const)[a.q1] +
    ({ 'creative-storyteller': 3, 'structured-play': 2, 'independent-explorer': 1 } as const)[a.q3]

  const dissociationScore =
    ({ 'frequent-dissociation': 3, 'occasional-detachment': 2, 'fully-present': 1 } as const)[a.q2] +
    ({ 'blank-slate': 3, 'context-dependent': 2, 'thought-rich': 1 } as const)[a.q4]

  if (fantasyScore >= 5 && dissociationScore >= 5) return 'dreamlike'
  if (fantasyScore >= 5 && dissociationScore <= 3) return 'electric'
  if (fantasyScore <= 3 && dissociationScore >= 5) return 'void'
  if (fantasyScore <= 3 && dissociationScore <= 3) return 'organic'
  return 'liminal'
}

function buildToken(a: PollAnswers): PollToken {
  const theme = deriveTheme(a)
  const profile = PROFILES[theme]
  const palette = PALETTES[theme]

  return {
    answers: { ...a },
    theme,
    palette,
    tone: profile.tone,
    archetype: profile.archetype,
    keywords: profile.keywords,
    adlibPrompt: `Write in a ${profile.tone} style. Draw from these thematic elements: ${profile.keywords.join(', ')}. The voice is that of ${profile.archetype}.`,
  }
}

export function usePollStore() {
  const isComplete = computed(
    () =>
      answers.value.q1 !== null &&
      answers.value.q2 !== null &&
      answers.value.q3 !== null &&
      answers.value.q4 !== null,
  )

  function setAnswer<K extends keyof PollAnswers>(question: K, answer: PollAnswers[K]) {
    answers.value[question] = answer
  }

  function submitPoll(): PollToken | null {
    if (!isComplete.value) return null
    const t = buildToken(answers.value)
    token.value = t
    localStorage.setItem(STORAGE_KEY, JSON.stringify(t))
    return t
  }

  function resetPoll() {
    answers.value = { q1: null, q2: null, q3: null, q4: null }
    token.value = null
    localStorage.removeItem(STORAGE_KEY)
  }

  return {
    answers,
    token,
    isComplete,
    setAnswer,
    submitPoll,
    resetPoll,
  }
}
