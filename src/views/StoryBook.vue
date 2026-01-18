<template>
  <div class="storybook-container min-h-screen p-8">
    <!-- File Upload Section -->
    <div v-if="!textLoaded" class="upload-section max-w-2xl mx-auto">
      <div class="text-center mb-8">
        <h1 class="text-4xl font-bold mb-4">Interactive Storybook</h1>
        <p class="text-lg text-gray-600">Upload a text file to experience it with animations and narration</p>
      </div>

      <div class="upload-area border-4 border-dashed border-gray-300 rounded-lg p-12 text-center hover:border-blue-400 transition-colors cursor-pointer"
           @click="triggerFileInput"
           @dragover.prevent="handleDragOver"
           @dragleave.prevent="handleDragLeave"
           @drop.prevent="handleDrop"
           :class="{ 'border-blue-400 bg-blue-50': isDragging }">
        <svg class="mx-auto h-12 w-12 text-gray-400 mb-4" stroke="currentColor" fill="none" viewBox="0 0 48 48">
          <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
        <p class="text-xl mb-2">Drop your .txt file here or click to browse</p>
        <p class="text-sm text-gray-500">Supports .txt files</p>
        <input
          ref="fileInput"
          type="file"
          accept=".txt"
          @change="handleFileSelect"
          class="hidden"
        />
      </div>

      <!-- Sample Text Option -->
      <div class="mt-8 text-center">
        <button
          @click="loadSampleText"
          class="px-6 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors">
          Load Sample: The Garden of Echoes
        </button>
      </div>
    </div>

    <!-- Story Display Section -->
    <div v-else class="story-section max-w-4xl mx-auto">
      <!-- Header Controls -->
      <div class="controls-header mb-8 flex justify-between items-center">
        <button
          @click="resetStory"
          class="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 transition-colors">
          ← Load Different Story
        </button>

        <div class="page-indicator text-lg font-semibold">
          Page {{ currentPageIndex + 1 }} of {{ pages.length }}
        </div>

        <div class="speech-controls flex gap-2">
          <button
            @click="toggleSpeech"
            :class="isSpeaking ? 'bg-red-500 hover:bg-red-600' : 'bg-blue-500 hover:bg-blue-600'"
            class="px-4 py-2 text-white rounded transition-colors">
            {{ isSpeaking ? '⏸ Pause' : '▶ Play Audio' }}
          </button>
          <button
            @click="stopSpeech"
            class="px-4 py-2 bg-gray-700 text-white rounded hover:bg-gray-800 transition-colors">
            ⏹ Stop
          </button>
        </div>
      </div>

      <!-- Story Content with Animation -->
      <div class="story-content relative min-h-[400px] bg-white rounded-lg shadow-2xl p-12">
        <transition :name="transitionName" mode="out-in">
          <div :key="currentPageIndex" class="text-content">
            <p
              v-for="(paragraph, index) in currentPageParagraphs"
              :key="index"
              class="mb-4 text-lg leading-relaxed animated-paragraph"
              :style="{ animationDelay: `${index * 0.1}s` }">
              {{ paragraph }}
            </p>
          </div>
        </transition>
      </div>

      <!-- Navigation Controls -->
      <div class="navigation-controls mt-8 flex justify-between items-center">
        <button
          @click="previousPage"
          :disabled="currentPageIndex === 0"
          :class="currentPageIndex === 0 ? 'opacity-50 cursor-not-allowed' : 'hover:bg-blue-600'"
          class="px-6 py-3 bg-blue-500 text-white rounded-lg transition-colors disabled:hover:bg-blue-500">
          ← Previous
        </button>

        <div class="progress-bar flex-1 mx-8 h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            class="progress-fill h-full bg-blue-500 transition-all duration-500"
            :style="{ width: `${progressPercentage}%` }">
          </div>
        </div>

        <button
          @click="nextPage"
          :disabled="currentPageIndex === pages.length - 1"
          :class="currentPageIndex === pages.length - 1 ? 'opacity-50 cursor-not-allowed' : 'hover:bg-blue-600'"
          class="px-6 py-3 bg-blue-500 text-white rounded-lg transition-colors disabled:hover:bg-blue-500">
          Next →
        </button>
      </div>

      <!-- Speed Control -->
      <div class="speed-control mt-6 text-center">
        <label class="mr-4 text-sm font-semibold">Speech Speed:</label>
        <input
          type="range"
          min="0.5"
          max="2"
          step="0.1"
          v-model.number="speechRate"
          @input="updateSpeechRate"
          class="w-48" />
        <span class="ml-4 text-sm">{{ speechRate.toFixed(1) }}x</span>
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
const transitionName = ref('slide-left')

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

  // Auto-start reading
  setTimeout(() => {
    startSpeech()
  }, 500)
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
    transitionName.value = 'slide-left'
    currentPageIndex.value++
    stopSpeech()
    setTimeout(() => startSpeech(), 300)
  }
}

const previousPage = () => {
  if (currentPageIndex.value > 0) {
    transitionName.value = 'slide-right'
    currentPageIndex.value--
    stopSpeech()
    setTimeout(() => startSpeech(), 300)
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
    // Auto-advance to next page
    if (currentPageIndex.value < pages.value.length - 1) {
      setTimeout(() => {
        nextPage()
      }, 1000)
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
.storybook-container {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
}

.upload-area {
  background-color: white;
  transition: all 0.3s ease;
}

.story-content {
  position: relative;
  overflow: hidden;
}

.animated-paragraph {
  animation: fadeInUp 0.6s ease forwards;
  opacity: 0;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Slide Transitions */
.slide-left-enter-active,
.slide-left-leave-active,
.slide-right-enter-active,
.slide-right-leave-active {
  transition: all 0.4s ease;
}

.slide-left-enter-from {
  opacity: 0;
  transform: translateX(50px);
}

.slide-left-leave-to {
  opacity: 0;
  transform: translateX(-50px);
}

.slide-right-enter-from {
  opacity: 0;
  transform: translateX(-50px);
}

.slide-right-leave-to {
  opacity: 0;
  transform: translateX(50px);
}

/* Progress bar animation */
.progress-fill {
  transition: width 0.5s ease;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .story-content {
    padding: 1.5rem;
  }

  .controls-header {
    flex-direction: column;
    gap: 1rem;
  }

  .navigation-controls {
    flex-direction: column;
    gap: 1rem;
  }

  .progress-bar {
    margin: 1rem 0;
  }
}
</style>
