<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useStoryStore } from '@/composables/useStoryStore'

const router = useRouter()
const {
  storyText,
  words,
  currentWord,
  currentIndex,
  progress,
  isPlaying,
  play,
  pause,
  seekToWord,
  backgroundMedia,
  isBackgroundVideo
} = useStoryStore()

const storyContainer = ref<HTMLElement | null>(null)

function togglePlayback() {
  if (isPlaying.value) {
    pause()
  } else {
    play()
  }
}

function handleKeydown(e: KeyboardEvent) {
  if (e.code !== 'Space') return
  const tag = (e.target as HTMLElement).tagName
  if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return
  e.preventDefault()
  togglePlayback()
}

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

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
  if (!storyText.value) {
    router.push('/')
  }
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <div class="reader" @click="togglePlayback">
    <!-- Background media layer — fills the viewport -->
    <div v-if="backgroundMedia" class="bg-layer">
      <video
        v-if="isBackgroundVideo"
        :src="backgroundMedia"
        autoplay
        loop
        muted
        playsinline
        class="bg-media"
      ></video>
      <img v-else :src="backgroundMedia" class="bg-media" alt="" />
    </div>

    <div v-if="words.length > 0" class="text-layer" @click.stop>
      <!-- Focus word — large, centered, blended into video -->
      <div class="focus-area">
        <span class="focus-word">{{ currentWord }}</span>
        <button class="play-toggle" @click="togglePlayback">
          {{ isPlaying ? '⏸' : '▶' }}
        </button>
      </div>

      <!-- Progress -->
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: `${progress}%` }"></div>
      </div>

      <!-- Story scroll — lower portion, soft blend -->
      <div ref="storyContainer" class="story-pane">
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

      <p class="hint">Space to play/pause &middot; click a word to seek</p>
    </div>

    <div v-else class="no-content" @click.stop>
      <p>No text loaded</p>
      <button @click="router.push('/')" class="back-btn">Go Back</button>
    </div>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Caveat:wght@400;500;600;700&display=swap');

/* ── Full-viewport reader frame ── */
.reader {
  position: relative;
  width: 100%;
  height: 100vh;
  overflow: hidden;
  background: #0a0a14;
}

/* ── Background media — fills frame ── */
.bg-layer {
  position: absolute;
  inset: 0;
  z-index: 0;
}

.bg-media {
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0.85;
}

/* ── Text layer — floats over video ── */
.text-layer {
  position: absolute;
  inset: 0;
  z-index: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 2rem 1.5rem;
  gap: 0.75rem;
}

/* ── Focus word — hero element ── */
.focus-area {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  padding: 1.5rem 2.5rem;
  border-radius: 1rem;
  backdrop-filter: blur(16px) brightness(1.1);
  background: rgba(15, 15, 35, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.focus-word {
  font-family: 'Caveat', cursive;
  font-size: clamp(2.5rem, 6vw, 4.5rem);
  font-weight: 700;
  color: rgba(226, 232, 240, 0.92);
  mix-blend-mode: screen;
  filter: drop-shadow(0 0 24px rgba(99, 102, 241, 0.3));
  min-width: 3rem;
  text-align: center;
  transition: filter 0.3s ease;
}

.play-toggle {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  width: 2.5rem;
  height: 2.5rem;
  font-size: 1rem;
  color: rgba(148, 163, 184, 0.7);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: color 0.2s, background 0.2s;
  mix-blend-mode: screen;
}

.play-toggle:hover {
  color: #e2e8f0;
  background: rgba(99, 102, 241, 0.2);
}

/* ── Progress bar ── */
.progress-bar {
  width: min(90%, 600px);
  height: 2px;
  background: rgba(255, 255, 255, 0.04);
  border-radius: 1px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: rgba(99, 102, 241, 0.6);
  transition: width 0.1s linear;
}

/* ── Story pane — lower region, blended ── */
.story-pane {
  width: min(90%, 700px);
  max-height: 30vh;
  overflow-y: auto;
  padding: 1.25rem 1.75rem;
  border-radius: 0.75rem;
  backdrop-filter: blur(12px) brightness(0.9);
  background: rgba(10, 10, 25, 0.35);
  border: 1px solid rgba(255, 255, 255, 0.04);
  scrollbar-width: thin;
  scrollbar-color: rgba(99, 102, 241, 0.3) transparent;
}

.story-pane::-webkit-scrollbar {
  width: 4px;
}

.story-pane::-webkit-scrollbar-track {
  background: transparent;
}

.story-pane::-webkit-scrollbar-thumb {
  background: rgba(99, 102, 241, 0.3);
  border-radius: 2px;
}

.story-text {
  font-family: 'Caveat', cursive;
  font-size: 1.5rem;
  font-weight: 500;
  line-height: 2;
  color: rgba(148, 163, 184, 0.5);
  mix-blend-mode: screen;
  word-wrap: break-word;
  overflow-wrap: break-word;
  white-space: pre-wrap;
  text-align: left;
  letter-spacing: 0.02em;
}

/* ── Word styles ── */
.word-span {
  cursor: pointer;
  padding: 0.1rem 0.15rem;
  border-radius: 0.15rem;
  transition: color 0.2s ease, text-shadow 0.2s ease, filter 0.2s ease;
  display: inline;
}

.word-span:hover {
  color: rgba(203, 213, 225, 0.7);
  text-shadow: 0 0 8px rgba(99, 102, 241, 0.3);
}

.word-span.active {
  color: rgba(226, 232, 240, 0.9);
  font-weight: 700;
  text-shadow: 0 0 16px rgba(99, 102, 241, 0.5), 0 0 40px rgba(99, 102, 241, 0.15);
  filter: drop-shadow(0 0 6px rgba(99, 102, 241, 0.25));
}

/* ── Hint ── */
.hint {
  font-size: 0.7rem;
  color: rgba(71, 85, 105, 0.6);
  text-align: center;
  mix-blend-mode: screen;
}

/* ── Mobile adjustments ── */
@media (max-width: 768px) {
  .text-layer {
    padding: 1rem 0.75rem;
  }

  .focus-area {
    padding: 1rem 1.5rem;
  }

  .story-pane {
    max-height: 25vh;
    padding: 1rem 1.25rem;
  }

  .story-text {
    font-size: 1.25rem;
    line-height: 1.8;
  }
}

/* ── No content fallback ── */
.no-content {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
  z-index: 1;
}

.no-content p {
  margin-bottom: 1rem;
}

.back-btn {
  background: transparent;
  color: #94a3b8;
  padding: 0.5rem 1rem;
  border: 1px solid #374151;
  border-radius: 0.5rem;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.2s;
}

.back-btn:hover {
  color: #e2e8f0;
  border-color: #6366f1;
}
</style>
