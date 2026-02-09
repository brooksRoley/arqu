<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useStoryStore } from '@/composables/useStoryStore'

const router = useRouter()
const { storyText, words, currentWord, currentIndex, progress, seekToWord } = useStoryStore()

const storyContainer = ref<HTMLElement | null>(null)
const backgroundMedia = ref<string | null>(null)
const isVideo = ref(false)

const scrollToCurrentWord = () => {
  nextTick(() => {
    const activeWord = document.querySelector('.word-span.active')
    if (activeWord && storyContainer.value) {
      const container = storyContainer.value
      const containerRect = container.getBoundingClientRect()
      const wordRect = activeWord.getBoundingClientRect()
      const scrollTarget =
        container.scrollTop +
        (wordRect.top - containerRect.top) -
        containerRect.height / 2 +
        wordRect.height / 2
      container.scrollTo({ top: scrollTarget, behavior: 'smooth' })
    }
  })
}

watch(currentIndex, () => {
  scrollToCurrentWord()
})

const handleMediaUpload = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    const url = URL.createObjectURL(file)
    backgroundMedia.value = url
    isVideo.value = file.type.startsWith('video/')
  }
}

const clearBackground = () => {
  if (backgroundMedia.value) {
    URL.revokeObjectURL(backgroundMedia.value)
    backgroundMedia.value = null
    isVideo.value = false
  }
}

onMounted(() => {
  if (!storyText.value) {
    router.push('/')
  }
})

onUnmounted(() => {
  clearBackground()
})
</script>

<template>
  <div class="reader">
    <!-- Background media layer -->
    <div v-if="backgroundMedia" class="background-media">
      <video
        v-if="isVideo"
        :src="backgroundMedia"
        autoplay
        loop
        muted
        playsinline
        class="bg-video"
      ></video>
      <img v-else :src="backgroundMedia" class="bg-image" alt="background" />
    </div>

    <div v-if="words.length > 0" class="reader-content">
      <div class="media-upload">
        <label class="upload-btn">
          {{ backgroundMedia ? 'Change Background' : 'Add Background' }}
          <input
            type="file"
            accept="image/gif,video/mp4,video/webm"
            @change="handleMediaUpload"
            hidden
          />
        </label>
        <button v-if="backgroundMedia" @click="clearBackground" class="clear-btn">Clear</button>
      </div>

      <!-- Word banner at top -->
      <div class="word-banner">
        <span class="banner-word">{{ currentWord }}</span>
      </div>

      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: `${progress}%` }"></div>
      </div>

      <!-- Full story text -->
      <div ref="storyContainer" class="story-container">
        <p class="story-text">
          <span
            v-for="(word, index) in words"
            :key="index"
            :class="['word-span', { active: index === currentIndex }]"
            @click="seekToWord(index)"
            >{{ word }}
          </span>
        </p>
      </div>
    </div>

    <div v-else class="no-content">
      <p>No text loaded</p>
      <button @click="router.push('/')" class="back-btn">Go Back</button>
    </div>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Caveat:wght@400;500;600;700&display=swap');

.reader {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: 100vh;
  overflow: hidden;
}

.background-media {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  pointer-events: none;
}

.bg-video,
.bg-image {
  width: 100%;
  height: 100%;
  object-fit: scale-down;
  opacity: 0.8;
}

.reader-content {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 900px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  margin-bottom: 100vh;
}

.word-banner {
  position: sticky;
  top: 0;
  background-color: rgba(31, 41, 55, 0.95);
  border-radius: 0.5rem;
  padding: 2rem;
  text-align: center;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
  z-index: 10;
  backdrop-filter: blur(8px);
  margin: 10vh 1rem;
}

.banner-word {
  font-family: 'Caveat', cursive;
  font-size: 3rem;
  font-weight: 700;
  color: #1a1a1a;
  background-color: #e2e8f0;
  padding: 0.25rem 1.5rem;
  border-radius: 0.25rem;
  display: inline-block;
  opacity: 1;
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

.story-container {
  width: 100%;
  max-height: 35vh;
  overflow-y: auto;
  background-color: rgba(17, 24, 39, 0.85);
  border-radius: 0.75rem;
  padding: 2rem 2.5rem;
  backdrop-filter: blur(4px);
  opacity: 0.4;
}

.story-text {
  font-family: 'Caveat', cursive;
  font-size: 1.75rem;
  font-weight: 500;
  line-height: 2.2;
  color: #cbd5e1;
  word-wrap: break-word;
  overflow-wrap: break-word;
  white-space: pre-wrap;
  text-align: left;
  letter-spacing: 0.02em;
}

.word-span {
  cursor: pointer;
  padding: 0.15rem 0.25rem;
  margin: 0 0.1rem;
  border-radius: 0.25rem;
  transition: all 0.15s ease;
  display: inline;
}

.word-span:hover {
  background-color: rgba(99, 102, 241, 0.3);
}

.word-span.active {
  background-color: #e2e8f0;
  color: #1a1a1a;
  font-weight: 700;
  box-shadow: 0 0 12px rgba(226, 232, 240, 0.6);
}

.media-upload {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  align-self: flex-end;
}

.upload-btn {
  background-color: rgba(55, 65, 81, 0.9);
  color: #94a3b8;
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  cursor: pointer;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.upload-btn:hover {
  background-color: rgba(75, 85, 99, 0.9);
  color: #e2e8f0;
}

.clear-btn {
  background-color: transparent;
  color: #f87171;
  padding: 0.5rem 0.75rem;
  border: 1px solid #f87171;
  border-radius: 0.5rem;
  cursor: pointer;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.clear-btn:hover {
  background-color: #f87171;
  color: #1a1a1a;
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
  z-index: 1;
}

.no-content p {
  margin-bottom: 1rem;
}
</style>
