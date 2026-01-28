<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const text = ref('')
const words = computed(() => text.value.split(/\s+/).filter(w => w.length > 0))
const currentIndex = ref(0)
const isPlaying = ref(false)
const wpm = ref(300)

let intervalId: number | null = null

const currentWord = computed(() => words.value[currentIndex.value] || '')
const progress = computed(() =>
  words.value.length > 0 ? ((currentIndex.value + 1) / words.value.length) * 100 : 0
)

const play = () => {
  if (currentIndex.value >= words.value.length - 1) {
    currentIndex.value = 0
  }
  isPlaying.value = true
  const interval = 60000 / wpm.value
  intervalId = window.setInterval(() => {
    if (currentIndex.value < words.value.length - 1) {
      currentIndex.value++
    } else {
      pause()
    }
  }, interval)
}

const pause = () => {
  isPlaying.value = false
  if (intervalId) {
    clearInterval(intervalId)
    intervalId = null
  }
}

const reset = () => {
  pause()
  currentIndex.value = 0
}

const goBack = () => {
  pause()
  router.push('/')
}

onMounted(() => {
  const storedText = sessionStorage.getItem('readerText')
  if (storedText) {
    text.value = storedText
  } else {
    router.push('/')
  }
})

onUnmounted(() => {
  pause()
})
</script>

<template>
  <div class="reader">
    <div v-if="words.length > 0" class="reader-content">
      <div class="word-display">
        <span class="word">{{ currentWord }}</span>
      </div>

      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: `${progress}%` }"></div>
      </div>

      <div class="controls">
        <button @click="reset" class="control-btn">Reset</button>
        <button @click="isPlaying ? pause() : play()" class="control-btn play-btn">
          {{ isPlaying ? 'Pause' : 'Play' }}
        </button>
        <div class="speed-control">
          <label>{{ wpm }} WPM</label>
          <input type="range" v-model.number="wpm" min="100" max="800" step="50" />
        </div>
      </div>

      <div class="stats">
        <span>Word {{ currentIndex + 1 }} of {{ words.length }}</span>
      </div>

      <button @click="goBack" class="back-btn">Load New Text</button>
    </div>

    <div v-else class="no-content">
      <p>No text loaded</p>
      <button @click="goBack" class="back-btn">Go Back</button>
    </div>
  </div>
</template>

<style scoped>
.reader {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: 60vh;
}

.reader-content {
  width: 100%;
  max-width: 600px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2rem;
}

.word-display {
  background-color: #1f2937;
  border-radius: 1rem;
  padding: 3rem 4rem;
  min-width: 300px;
  text-align: center;
}

.word {
  font-size: 3rem;
  font-weight: bold;
  color: #e2e8f0;
}

.progress-bar {
  width: 100%;
  height: 4px;
  background-color: #374151;
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background-color: #6366f1;
  transition: width 0.1s linear;
}

.controls {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
  justify-content: center;
}

.control-btn {
  background-color: #374151;
  color: #e2e8f0;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.control-btn:hover {
  background-color: #4b5563;
}

.play-btn {
  background-color: #6366f1;
  min-width: 100px;
}

.play-btn:hover {
  background-color: #4f46e5;
}

.speed-control {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
}

.speed-control label {
  font-size: 0.875rem;
  color: #94a3b8;
}

.speed-control input {
  width: 120px;
}

.stats {
  color: #64748b;
  font-size: 0.875rem;
}

.back-btn {
  background-color: transparent;
  color: #94a3b8;
  padding: 0.5rem 1rem;
  border: 1px solid #374151;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.2s;
}

.back-btn:hover {
  color: #e2e8f0;
  border-color: #6366f1;
}

.no-content {
  text-align: center;
  color: #94a3b8;
}

.no-content p {
  margin-bottom: 1rem;
}
</style>
