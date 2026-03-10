<template>
  <div class="p-4 max-w-4xl mx-auto">
    <!-- Guide Selection -->
    <div v-if="!sessionActive">
      <h1 class="text-3xl font-bold mb-2">Trance Guide</h1>
      <p class="text-sm mb-6 opacity-70">
        Guide your partner through calming emotional states with narrated scripts and frequency guidance
      </p>

      <!-- Trance Programs -->
      <div class="mb-8">
        <h2 class="text-xl font-semibold mb-4">Select a Guided Experience</h2>
        <div class="space-y-3">
          <div
            v-for="program in programs"
            :key="program.id"
            @click="selectProgram(program)"
            class="border p-4 cursor-pointer hover:border-blue-500 transition-colors">
            <div class="flex justify-between items-start mb-2">
              <h3 class="font-semibold text-lg">{{ program.name }}</h3>
              <span class="text-xs px-2 py-1 bg-gray-100 rounded">
                {{ program.duration }}
              </span>
            </div>
            <p class="text-sm mb-3">{{ program.description }}</p>
            <div class="text-xs space-y-1">
              <div><strong>Target State:</strong> {{ program.targetState }}</div>
              <div><strong>Frequency Range:</strong> {{ program.frequencyRange }}</div>
              <div class="opacity-70">{{ program.effect }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Custom Upload -->
      <div class="border-t pt-6">
        <h2 class="text-xl font-semibold mb-3">Custom Script</h2>
        <div
          class="border-2 border-dashed p-6 cursor-pointer"
          @click="triggerFileInput"
          @dragover.prevent="handleDragOver"
          @dragleave.prevent="handleDragLeave"
          @drop.prevent="handleDrop"
          :class="{ 'border-blue-500': isDragging }">
          <p class="text-sm">Upload your own .txt script</p>
          <input ref="fileInput" type="file" accept=".txt" @change="handleFileSelect" class="hidden" />
        </div>
      </div>
    </div>

    <!-- Active Session -->
    <div v-else>
      <!-- Session Header -->
      <div class="mb-6 pb-4 border-b">
        <div class="flex justify-between items-start mb-3">
          <div>
            <h1 class="text-2xl font-bold">{{ currentProgram?.name || 'Custom Session' }}</h1>
            <p class="text-sm opacity-70 mt-1">{{ currentStateInfo.description }}</p>
          </div>
          <button @click="endSession" class="px-3 py-1 border text-sm">End Session</button>
        </div>

        <!-- State Indicator -->
        <div class="flex items-center gap-3 text-sm">
          <span class="font-semibold">Current State:</span>
          <span class="px-3 py-1 bg-blue-100 rounded">{{ currentStateInfo.name }}</span>
          <span class="opacity-70">{{ currentStateInfo.frequency }}</span>
        </div>
      </div>

      <!-- Why This Works -->
      <div v-if="currentStateInfo.explanation" class="mb-4 p-4 bg-gray-50 border-l-4 border-blue-500">
        <div class="text-sm font-semibold mb-1">💡 Why This Works</div>
        <p class="text-sm">{{ currentStateInfo.explanation }}</p>
      </div>

      <!-- Script Content -->
      <div class="border p-6 min-h-[300px] mb-4 bg-white">
        <transition name="fade" mode="out-in">
          <div :key="currentPageIndex">
            <p v-for="(paragraph, index) in currentPageParagraphs" :key="index" class="mb-4 leading-relaxed">
              {{ paragraph }}
            </p>
          </div>
        </transition>
      </div>

      <!-- Controls -->
      <div class="space-y-4">
        <!-- Playback Controls -->
        <div class="flex items-center justify-between flex-wrap gap-3 pb-3 border-b">
          <div class="flex gap-2">
            <button @click="toggleSpeech" class="px-4 py-2 border" :class="{ 'bg-blue-500 text-white': isSpeaking }">
              {{ isSpeaking ? '⏸ Pause Narration' : '▶ Start Narration' }}
            </button>
            <button @click="stopSpeech" class="px-4 py-2 border">⏹ Stop</button>
          </div>
          <div class="text-sm">
            <span class="opacity-70">Voice Speed:</span>
            <input
              type="range"
              min="0.5"
              max="1.5"
              step="0.1"
              v-model.number="speechRate"
              @input="updateSpeechRate"
              class="mx-2 w-24" />
            <span>{{ speechRate.toFixed(1) }}x</span>
          </div>
        </div>

        <!-- Navigation -->
        <div class="flex items-center gap-3">
          <button @click="previousPage" :disabled="currentPageIndex === 0" class="px-4 py-2 border disabled:opacity-30">
            ← Previous
          </button>
          <div class="flex-1">
            <div class="flex justify-between text-xs mb-1">
              <span>Section {{ currentPageIndex + 1 }} of {{ pages.length }}</span>
              <span>{{ Math.round(progressPercentage) }}%</span>
            </div>
            <div class="h-2 bg-gray-100 border">
              <div class="h-full bg-blue-500 transition-all" :style="{ width: `${progressPercentage}%` }"></div>
            </div>
          </div>
          <button
            @click="nextPage"
            :disabled="currentPageIndex === pages.length - 1"
            class="px-4 py-2 border disabled:opacity-30">
            Next →
          </button>
        </div>

        <!-- Guidance Tips -->
        <div class="text-xs p-3 bg-blue-50 border border-blue-200">
          <strong>Partner Guidance:</strong>
          <span v-if="!isSpeaking">Start narration and speak slowly, maintaining a calm, steady voice.</span>
          <span v-else-if="currentPageIndex < pages.length / 3">
            Allow them to settle in. Watch for relaxed breathing and reduced muscle tension.
          </span>
          <span v-else-if="currentPageIndex < (pages.length * 2) / 3">
            They should be deeply relaxed now. Keep your voice soft and consistent.
          </span>
          <span v-else> Prepare for gentle awakening. Gradually increase your energy as you approach the end. </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue'

// Types
interface TranceProgram {
  id: string
  name: string
  description: string
  duration: string
  targetState: string
  frequencyRange: string
  effect: string
  content?: string
  states: TranceState[]
}

interface TranceState {
  name: string
  frequency: string
  description: string
  explanation: string
}

// Predefined Programs
const programs: TranceProgram[] = [
  {
    id: 'deep-calm',
    name: 'Deep Calm Induction',
    description: 'Gentle progression from alert awareness to deep relaxation',
    duration: '15-20 min',
    targetState: 'Theta (4-8 Hz)',
    frequencyRange: 'Beta → Alpha → Theta',
    effect: 'Promotes deep relaxation, stress relief, and meditative states',
    states: [
      {
        name: 'Alert Relaxation',
        frequency: 'Alpha (8-12 Hz)',
        description: 'Calm but aware, preparing to relax',
        explanation:
          'Alpha waves occur during wakeful relaxation. This frequency helps transition from active thinking to calm receptivity, similar to closing your eyes and taking deep breaths.'
      },
      {
        name: 'Light Trance',
        frequency: 'Low Alpha / High Theta (7-9 Hz)',
        description: 'Drifting into deeper relaxation',
        explanation:
          'The bridge between consciousness and subconscious. This state enhances suggestibility and creativity, often experienced just before falling asleep.'
      },
      {
        name: 'Deep Trance',
        frequency: 'Theta (4-7 Hz)',
        description: 'Deeply relaxed, highly receptive',
        explanation:
          'Theta waves are associated with deep meditation, REM sleep, and hypnosis. In this state, the subconscious mind is highly receptive to positive suggestions and healing.'
      },
      {
        name: 'Awakening',
        frequency: 'Theta → Alpha → Beta',
        description: 'Gentle return to alertness',
        explanation:
          'Gradually increasing frequencies help transition back to normal waking consciousness, ensuring the person feels refreshed and grounded.'
      }
    ]
  },
  {
    id: 'quick-reset',
    name: 'Quick Reset',
    description: 'Brief relaxation cycle for stress relief',
    duration: '5-8 min',
    targetState: 'Alpha (8-12 Hz)',
    frequencyRange: 'Beta → Alpha → Beta',
    effect: 'Reduces anxiety, clears mental fog, restores focus',
    states: [
      {
        name: 'Settling',
        frequency: 'Alpha (10-12 Hz)',
        description: 'Releasing tension and worry',
        explanation:
          'High alpha waves promote relaxed alertness. This frequency is optimal for stress reduction while maintaining awareness, like a mental reset button.'
      },
      {
        name: 'Calm Focus',
        frequency: 'Alpha (8-10 Hz)',
        description: 'Centered and peaceful',
        explanation:
          'Mid-range alpha waves enhance present-moment awareness and emotional balance. This state combines relaxation with mental clarity.'
      },
      {
        name: 'Re-energizing',
        frequency: 'Alpha → Beta',
        description: 'Returning refreshed and focused',
        explanation:
          'Transitioning back to beta frequencies restores active thinking and energy, but with the calm foundation of the alpha state still present.'
      }
    ]
  },
  {
    id: 'sample-garden',
    name: 'The Garden of Echoes',
    description: 'Narrative journey through peaceful meditation',
    duration: '20-25 min',
    targetState: 'Theta (4-8 Hz)',
    frequencyRange: 'Full spectrum relaxation',
    effect: 'Story-based deep relaxation with vivid imagery',
    content: 'TheGardenofEchoes.txt',
    states: [
      {
        name: 'Story Immersion',
        frequency: 'Alpha-Theta (6-10 Hz)',
        description: 'Entering the narrative world',
        explanation:
          'Storytelling naturally induces alpha-theta states as the mind visualizes and emotionally engages. This creates deep absorption similar to meditation.'
      },
      {
        name: 'Deep Journey',
        frequency: 'Theta (4-7 Hz)',
        description: 'Fully immersed in the experience',
        explanation:
          'As the story unfolds, theta waves deepen, allowing powerful emotional processing and subconscious integration of the narrative themes.'
      },
      {
        name: 'Integration',
        frequency: 'Theta → Alpha',
        description: 'Processing and returning',
        explanation:
          'The story conclusion guides back to alpha waves, helping integrate insights and experiences while gently returning to awareness.'
      }
    ]
  }
]

// State
const fileInput = ref<HTMLInputElement | null>(null)
const isDragging = ref(false)
const sessionActive = ref(false)
const currentProgram = ref<TranceProgram | null>(null)
const pages = ref<string[]>([])
const currentPageIndex = ref(0)
const isSpeaking = ref(false)
const speechRate = ref(0.8) // Slower default for calm delivery

// Speech Synthesis
let speechSynthesis: SpeechSynthesis | null = null
let currentUtterance: SpeechSynthesisUtterance | null = null

if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
  speechSynthesis = window.speechSynthesis
}

// Computed
const currentStateInfo = computed(() => {
  if (!currentProgram.value) {
    return {
      name: 'Neutral',
      frequency: 'N/A',
      description: 'Custom session',
      explanation: ''
    }
  }

  const states = currentProgram.value.states
  const progress = currentPageIndex.value / Math.max(pages.value.length - 1, 1)

  // Map progress to state
  if (progress < 0.25) return states[0] || states[0]
  if (progress < 0.6) return states[1] || states[0]
  if (progress < 0.9) return states[2] || states[1]
  return states[3] || states[states.length - 1]
})

const currentPageParagraphs = computed(() => {
  if (!pages.value[currentPageIndex.value]) return []
  return pages.value[currentPageIndex.value].split('\n').filter((p) => p.trim().length > 0)
})

const progressPercentage = computed(() => {
  if (pages.value.length === 0) return 0
  return ((currentPageIndex.value + 1) / pages.value.length) * 100
})

// Program Selection
const selectProgram = async (program: TranceProgram) => {
  currentProgram.value = program

  if (program.content) {
    // Load from asset file
    try {
      const response = await fetch(new URL(`@/assets/${program.content}`, import.meta.url).href)
      const text = await response.text()
      loadText(text)
    } catch (error) {
      console.error('Error loading program content:', error)
      alert('Failed to load program content')
    }
  } else {
    // Generate default calming script
    loadText(generateDefaultScript(program))
  }
}

const generateDefaultScript = (program: TranceProgram): string => {
  const scripts: Record<string, string> = {
    'deep-calm': `Welcome. Find a comfortable position and close your eyes.

Take a deep breath in... and slowly exhale. Feel your body beginning to relax.

With each breath, notice the gentle rise and fall of your chest. Your shoulders softening. Your jaw loosening.

You are safe. You are calm. You are exactly where you need to be.

Let any thoughts drift by like clouds in the sky. You don't need to hold onto them. Just observe and let go.

Your body is becoming heavier, more relaxed. Sinking deeper into comfort.

Notice the feeling of deep peace spreading through you. From the top of your head, flowing down through your neck, your shoulders, your arms.

This peaceful feeling fills your chest, your stomach, flowing down through your legs to your toes.

You are completely relaxed. Deeply calm. Perfectly at peace.

Stay here as long as you need. There is no rush. Just peace and calm.

When you're ready, take a deep breath. Begin to notice your surroundings. Gently wiggle your fingers and toes.

Take your time. And when you're ready, open your eyes. Feeling refreshed, calm, and centered.`,

    'quick-reset': `Take a moment to pause. Right now, in this moment, you can let go.

Breathe in deeply... hold for a moment... and release.

Again. Breathe in calm... hold... and breathe out tension.

Feel your shoulders drop. Your face soften. Your mind clear.

You don't need to carry everything right now. Just be here. Just breathe.

Notice how your body feels lighter. Your thoughts quieter. Your spirit calmer.

One more deep breath. In... and out.

Good. You are reset. You are ready. You are calm.

Open your eyes when ready, feeling refreshed and focused.`
  }

  return scripts[program.id] || 'Take a moment to breathe deeply and relax.'
}

// File Upload
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
    currentProgram.value = null // Custom program
    loadText(text)
  }
  reader.readAsText(file)
}

// Text Processing
const loadText = (text: string) => {
  const paragraphs = text.split(/\n\n+/)
  const pagesArray: string[] = []
  let currentPage = ''

  paragraphs.forEach((para) => {
    const trimmedPara = para.trim()
    if (trimmedPara.length === 0) return

    if (currentPage.length + trimmedPara.length > 600) {
      if (currentPage) pagesArray.push(currentPage.trim())
      currentPage = trimmedPara
    } else {
      currentPage += (currentPage ? '\n\n' : '') + trimmedPara
    }
  })

  if (currentPage.trim().length > 0) {
    pagesArray.push(currentPage.trim())
  }

  pages.value = pagesArray
  sessionActive.value = true
  currentPageIndex.value = 0
  setTimeout(() => startSpeech(), 500)
}

const endSession = () => {
  stopSpeech()
  sessionActive.value = false
  currentProgram.value = null
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
    setTimeout(() => startSpeech(), 300)
  }
}

const previousPage = () => {
  if (currentPageIndex.value > 0) {
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
  currentUtterance.pitch = 0.9 // Slightly lower for calming effect
  currentUtterance.volume = 1

  currentUtterance.onend = () => {
    isSpeaking.value = false
    if (currentPageIndex.value < pages.value.length - 1) {
      setTimeout(() => nextPage(), 2000) // Longer pause between sections
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
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
