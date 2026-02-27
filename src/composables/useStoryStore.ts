import { ref, computed } from 'vue'

// Shared state — module-level so it persists across all consumers
const storyText = ref(`Pick your next story with 'Edit Text'.`)
const currentIndex = ref(0)
const isPlaying = ref(false)

// Background media state
const backgroundMedia = ref<string | null>(null)
const isBackgroundVideo = ref(false)

let intervalId: number | null = null
const wpm = ref(250) // words per minute

const words = computed(() => storyText.value.split(/\s+/).filter((w) => w.length > 0))
const currentWord = computed(() => words.value[currentIndex.value] || '')
const progress = computed(() =>
  words.value.length > 0 ? ((currentIndex.value + 1) / words.value.length) * 100 : 0
)

function advanceWord() {
  if (currentIndex.value < words.value.length - 1) {
    currentIndex.value++
  } else {
    reset()
    play()
  }
}

function play() {
  if (currentIndex.value >= words.value.length - 1) {
    currentIndex.value = 0
  }

  isPlaying.value = true
  const msPerWord = 60000 / wpm.value
  intervalId = window.setInterval(advanceWord, msPerWord)
}

function pause() {
  isPlaying.value = false
  if (intervalId) {
    clearInterval(intervalId)
    intervalId = null
  }
}

function reset() {
  pause()
  currentIndex.value = 0
}

function seekToWord(index: number) {
  currentIndex.value = index
}

function setStoryText(text: string) {
  pause()
  currentIndex.value = 0
  storyText.value = text
}

function clearStoryText() {
  setStoryText('')
}

function setBackgroundMedia(url: string, video: boolean) {
  if (backgroundMedia.value) {
    URL.revokeObjectURL(backgroundMedia.value)
  }
  backgroundMedia.value = url
  isBackgroundVideo.value = video
}

function clearBackgroundMedia() {
  if (backgroundMedia.value) {
    URL.revokeObjectURL(backgroundMedia.value)
    backgroundMedia.value = null
    isBackgroundVideo.value = false
  }
}

function setWpm(value: number) {
  wpm.value = value
  if (isPlaying.value) {
    pause()
    play()
  }
}

export function useStoryStore() {
  return {
    storyText,
    words,
    currentWord,
    currentIndex,
    progress,
    isPlaying,
    wpm,
    setStoryText,
    clearStoryText,
    play,
    pause,
    reset,
    seekToWord,
    setWpm,
    backgroundMedia,
    isBackgroundVideo,
    setBackgroundMedia,
    clearBackgroundMedia
  }
}
