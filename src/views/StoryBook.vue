<template>
  <div class="p-4 max-w-3xl mx-auto">
    <!-- File Upload -->
    <div v-if="!textLoaded">
      <h1 class="text-2xl font-bold mb-4">StoryBook</h1>
      <div
        class="border-2 border-dashed p-8 mb-4 cursor-pointer"
        @click="triggerFileInput"
        @dragover.prevent="handleDragOver"
        @dragleave.prevent="handleDragLeave"
        @drop.prevent="handleDrop"
        :class="{ 'border-blue-500': isDragging }">
        <p class="mb-2">Drop .txt file or click to browse</p>
        <input ref="fileInput" type="file" accept=".txt" @change="handleFileSelect" class="hidden" />
      </div>
      <button @click="loadSampleText" class="px-4 py-2 border">Load Sample</button>
    </div>

    <!-- Story Display -->
    <div v-else>
      <div class="mb-4 flex justify-between items-center flex-wrap gap-2">
        <button @click="resetStory" class="px-3 py-1 border">← Back</button>
        <span class="text-sm">Page {{ currentPageIndex + 1 }} / {{ pages.length }}</span>
        <div class="flex gap-2">
          <button @click="toggleSpeech" class="px-3 py-1 border">
            {{ isSpeaking ? '⏸' : '▶' }}
          </button>
          <button @click="stopSpeech" class="px-3 py-1 border">⏹</button>
        </div>
      </div>

      <div class="border p-6 min-h-[300px] mb-4">
        <transition name="fade" mode="out-in">
          <div :key="currentPageIndex">
            <p v-for="(paragraph, index) in currentPageParagraphs" :key="index" class="mb-4">
              {{ paragraph }}
            </p>
          </div>
        </transition>
      </div>

      <div class="flex items-center gap-4 mb-4">
        <button @click="previousPage" :disabled="currentPageIndex === 0" class="px-4 py-2 border disabled:opacity-50">
          ← Prev
        </button>
        <div class="flex-1 h-1 bg-gray-200">
          <div class="h-full bg-gray-800" :style="{ width: `${progressPercentage}%` }"></div>
        </div>
        <button
          @click="nextPage"
          :disabled="currentPageIndex === pages.length - 1"
          class="px-4 py-2 border disabled:opacity-50">
          Next →
        </button>
      </div>

      <div class="text-sm">
        <label>Speed: </label>
        <input type="range" min="0.5" max="2" step="0.1" v-model.number="speechRate" @input="updateSpeechRate" class="mx-2" />
        <span>{{ speechRate.toFixed(1) }}x</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue'

// State
const fileInput = ref<HTMLInputElement | null>(null)
const isDragging = ref(false)
const textLoaded = ref(false)
const fullText = ref('')
const pages = ref<string[]>([])
const currentPageIndex = ref(0)
const isSpeaking = ref(false)
const speechRate = ref(1.0)

// Speech Synthesis
let speechSynthesis: SpeechSynthesis | null = null
let currentUtterance: SpeechSynthesisUtterance | null = null

if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
  speechSynthesis = window.speechSynthesis
}

// Computed
const currentPageParagraphs = computed(() => {
  if (!pages.value[currentPageIndex.value]) return []
  return pages.value[currentPageIndex.value]
    .split('\n')
    .filter(p => p.trim().length > 0)
})

const progressPercentage = computed(() => {
  if (pages.value.length === 0) return 0
  return ((currentPageIndex.value + 1) / pages.value.length) * 100
})

// File Upload Handlers
const triggerFileInput = () => {
  fileInput.value?.click()
}

const handleDragOver = () => {
  isDragging.value = true
}

const handleDragLeave = () => {
  isDragging.value = false
}

const handleDrop = (event: DragEvent) => {
  isDragging.value = false
  const files = event.dataTransfer?.files
  if (files && files.length > 0) {
    processFile(files[0])
  }
}

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  const files = target.files
  if (files && files.length > 0) {
    processFile(files[0])
  }
}

const processFile = (file: File) => {
  if (!file.name.endsWith('.txt')) {
    alert('Please upload a .txt file')
    return
  }

  const reader = new FileReader()
  reader.onload = (e) => {
    const text = e.target?.result as string
    loadText(text)
  }
  reader.readAsText(file)
}

const loadSampleText = async () => {
  try {
    const response = await fetch(new URL('@/assets/TheGardenofEchoes.txt', import.meta.url).href)
    const text = await response.text()
    loadText(text)
  } catch (error) {
    console.error('Error loading sample text:', error)
    alert('Failed to load sample text')
  }
}

// Text Processing
const loadText = (text: string) => {
  fullText.value = text
  // Split text into pages by double line breaks or every ~500 characters
  const paragraphs = text.split(/\n\n+/)

  // Group paragraphs into pages (approximately 3-5 paragraphs per page)
  const pagesArray: string[] = []
  let currentPage = ''

  paragraphs.forEach((para, index) => {
    const trimmedPara = para.trim()
    if (trimmedPara.length === 0) return

    if (currentPage.length + trimmedPara.length > 800 || (currentPage && index % 3 === 0)) {
      pagesArray.push(currentPage.trim())
      currentPage = trimmedPara
    } else {
      currentPage += (currentPage ? '\n\n' : '') + trimmedPara
    }
  })

  if (currentPage.trim().length > 0) {
    pagesArray.push(currentPage.trim())
  }

  pages.value = pagesArray
  textLoaded.value = true
  currentPageIndex.value = 0
  setTimeout(() => startSpeech(), 300)
}

const resetStory = () => {
  stopSpeech()
  textLoaded.value = false
  fullText.value = ''
  pages.value = []
  currentPageIndex.value = 0
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

// Navigation
const nextPage = () => {
  if (currentPageIndex.value < pages.value.length - 1) {
    currentPageIndex.value++
    stopSpeech()
    setTimeout(() => startSpeech(), 200)
  }
}

const previousPage = () => {
  if (currentPageIndex.value > 0) {
    currentPageIndex.value--
    stopSpeech()
    setTimeout(() => startSpeech(), 200)
  }
}

// Text-to-Speech
const startSpeech = () => {
  if (!speechSynthesis || !pages.value[currentPageIndex.value]) return

  stopSpeech()

  const text = pages.value[currentPageIndex.value]
  currentUtterance = new SpeechSynthesisUtterance(text)
  currentUtterance.rate = speechRate.value
  currentUtterance.pitch = 1
  currentUtterance.volume = 1

  currentUtterance.onend = () => {
    isSpeaking.value = false
    if (currentPageIndex.value < pages.value.length - 1) {
      setTimeout(() => nextPage(), 500)
    }
  }

  currentUtterance.onerror = () => {
    isSpeaking.value = false
  }

  speechSynthesis.speak(currentUtterance)
  isSpeaking.value = true
}

const stopSpeech = () => {
  if (!speechSynthesis) return
  speechSynthesis.cancel()
  isSpeaking.value = false
}

const toggleSpeech = () => {
  if (isSpeaking.value) {
    stopSpeech()
  } else {
    startSpeech()
  }
}

const updateSpeechRate = () => {
  if (currentUtterance && speechSynthesis && isSpeaking.value) {
    // Restart speech with new rate
    const wasPlaying = isSpeaking.value
    stopSpeech()
    if (wasPlaying) {
      setTimeout(() => startSpeech(), 100)
    }
  }
}

// Cleanup
onUnmounted(() => {
  stopSpeech()
})

// Watch for page changes
watch(currentPageIndex, () => {
  // Page change handled in navigation functions
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
