import { ref, computed, watch, onUnmounted } from 'vue'
import { useStoryStore } from './useStoryStore'
import { categories, pickRandom } from './useTranceCategories'

/**
 * Unified text overlay composable.
 *
 * When the reader has text loaded (useStoryStore), it feeds from that —
 * respecting phrase mode, trance sync, and playback state.
 *
 * When no reader text exists, it falls back to cycling trance category
 * words on a timer (the same "Focus / Relaxation / Deepening / …" flow
 * that spiral and trance-canvas used to do independently).
 *
 * Visual views (SpiralView, TranceCanvas, WebAudio) consume this
 * instead of rolling their own word systems.
 */
export function useTextOverlay() {
  const store = useStoryStore()

  // ── Reader mode: text is loaded ──────────────────────────────────
  const hasReaderText = computed(() => store.words.value.length > 0)

  // ── Fallback mode: trance category cycling ───────────────────────
  const fallbackWord = ref('')
  const fallbackCategory = ref('')
  const fallbackCatKey = ref('focus')
  const fallbackVisible = ref(true)
  let fallbackTimer: ReturnType<typeof setInterval> | null = null
  const FALLBACK_INTERVAL = 3500 // ms between words
  const FADE_MS = 600

  let fbCatIdx = 0
  let fbWordIdx = 0
  const catKeys = Object.keys(categories)

  function initFallback() {
    const key = catKeys[0]
    fallbackCatKey.value = key
    fallbackCategory.value = categories[key].label
    fallbackWord.value = categories[key].words[0]
    fallbackVisible.value = true
    fbCatIdx = 0
    fbWordIdx = 0
  }

  function advanceFallback() {
    fallbackVisible.value = false
    setTimeout(() => {
      fbWordIdx++
      const cat = categories[catKeys[fbCatIdx]]
      if (fbWordIdx >= cat.words.length) {
        fbWordIdx = 0
        fbCatIdx = (fbCatIdx + 1) % catKeys.length
      }
      const key = catKeys[fbCatIdx]
      fallbackCatKey.value = key
      fallbackCategory.value = categories[key].label
      fallbackWord.value = categories[key].words[fbWordIdx]
      fallbackVisible.value = true
    }, FADE_MS)
  }

  function skipFallbackCategory() {
    fbWordIdx = 0
    fbCatIdx = (fbCatIdx + 1) % catKeys.length
    fallbackVisible.value = false
    setTimeout(() => {
      const key = catKeys[fbCatIdx]
      fallbackCatKey.value = key
      fallbackCategory.value = categories[key].label
      fallbackWord.value = categories[key].words[0]
      fallbackVisible.value = true
    }, FADE_MS)
  }

  function startFallbackCycle() {
    stopFallbackCycle()
    initFallback()
    fallbackTimer = setInterval(advanceFallback, FALLBACK_INTERVAL)
  }

  function stopFallbackCycle() {
    if (fallbackTimer) {
      clearInterval(fallbackTimer)
      fallbackTimer = null
    }
  }

  // Auto-start/stop fallback based on reader text presence
  watch(hasReaderText, (has) => {
    if (has) {
      stopFallbackCycle()
    } else {
      startFallbackCycle()
    }
  }, { immediate: true })

  onUnmounted(() => {
    stopFallbackCycle()
  })

  // ── Unified output ───────────────────────────────────────────────

  /** The text to display — reader phrase/word, or fallback trance word */
  const displayText = computed(() => {
    if (hasReaderText.value) {
      return store.phraseMode.value ? store.currentPhrase.value : store.currentWord.value
    }
    return fallbackWord.value
  })

  /** Category/section label — empty for reader text, category name for fallback */
  const displayLabel = computed(() => {
    if (hasReaderText.value) return ''
    return fallbackCategory.value
  })

  /** Current trance category key (for visual theming). Falls back to 'focus'. */
  const activeCatKey = computed(() => {
    if (hasReaderText.value) return 'focus'
    return fallbackCatKey.value
  })

  /** Whether the text is in a visible state (for CSS transitions) */
  const isVisible = computed(() => {
    if (hasReaderText.value) return true // reader handles its own transitions
    return fallbackVisible.value
  })

  /** Whether we're in reader mode vs fallback */
  const isReaderMode = hasReaderText

  /** Reader progress (0–100), or null in fallback mode */
  const readerProgress = computed(() => {
    if (!hasReaderText.value) return null
    return store.progress.value
  })

  // ── Controls ─────────────────────────────────────────────────────

  /** Toggle reader playback, or skip fallback category */
  function toggleOrSkip() {
    if (hasReaderText.value) {
      if (store.isPlaying.value) store.pause()
      else store.play()
    } else {
      skipFallbackCategory()
    }
  }

  return {
    // Display
    displayText,
    displayLabel,
    activeCatKey,
    isVisible,
    isReaderMode,
    readerProgress,

    // Reader passthrough
    isPlaying: store.isPlaying,
    phraseMode: store.phraseMode,
    tranceSynced: store.tranceSynced,

    // Controls
    toggleOrSkip,
    skipFallbackCategory,
    play: store.play,
    pause: store.pause,
  }
}
