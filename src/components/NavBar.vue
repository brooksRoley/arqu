<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useStoryStore } from '@/composables/useStoryStore'

const router = useRouter()
const {
  storyText,
  words,
  currentIndex,
  isPlaying,
  setStoryText,
  play,
  pause,
  reset
} = useStoryStore()

// Dock visibility state
const isActive = ref(false)
const isHovered = ref(false)
let hideTimeout: number | null = null

// Text edit modal state
const showTextModal = ref(false)
const textInputValue = ref('')
const fileName = ref('')

const navRoutes = computed(() => {
  return router
    .getRoutes()
    .filter((route) => route.name && route.path !== '/:pathMatch(.*)*')
    .map((route) => ({
      name: route.name as string,
      path: route.path,
      label: formatRouteName(route.name as string),
      icon: getRouteIcon(route.name as string)
    }))
})

function formatRouteName(name: string): string {
  return name
    .replace(/([A-Z])/g, ' $1')
    .replace(/^./, (str) => str.toUpperCase())
    .trim()
}

function getRouteIcon(name: string): string {
  const icons: Record<string, string> = {
    home: '🏠',
    reader: '📖',
    zeromind: '🌀',
    resume: '💧'
  }
  return icons[name] || '📄'
}

// Background music state
const audioTracks = [
  { name: 'Floating', file: 'floating.mp3' },
  { name: 'Coding Night', file: 'coding-night.mp3' },
  { name: 'Good Doll', file: 'GoodDoll_ServeNow_EmptyForMe copy.mp3' },
  { name: 'Kitty Queen', file: 'KittyQueen copy.mp3' },
  { name: 'Rack Em Up', file: 'rackEmUp copy.mp3' },
  { name: 'Voice of Magic p1', file: 'voiceofmagicp1 copy.mp3' },
  { name: 'Voice of Magic p2', file: 'voiceofmagicp2 copy.mp3' }
]
const currentTrackIndex = ref(0)
const musicPlaying = ref(false)
const showTrackPicker = ref(false)
const audioElement = ref<HTMLAudioElement | null>(null)

function initAudio() {
  audioElement.value = new Audio(`/audio/${audioTracks[currentTrackIndex.value].file}`)
  audioElement.value.loop = true
  audioElement.value.volume = 0.3
  audioElement.value.play().then(() => {
    musicPlaying.value = true
  }).catch(() => {
    // Autoplay blocked by browser; user must interact first
    musicPlaying.value = false
  })
}

function toggleMusic() {
  if (!audioElement.value) {
    initAudio()
    return
  }

  if (musicPlaying.value) {
    audioElement.value.pause()
    musicPlaying.value = false
  } else {
    audioElement.value.play()
    musicPlaying.value = true
  }
}

function selectTrack(index: number) {
  if (index === currentTrackIndex.value && musicPlaying.value) {
    showTrackPicker.value = false
    return
  }
  currentTrackIndex.value = index
  if (audioElement.value) {
    audioElement.value.pause()
  }
  audioElement.value = new Audio(`/audio/${audioTracks[index].file}`)
  audioElement.value.loop = true
  audioElement.value.volume = 0.3
  audioElement.value.play()
  musicPlaying.value = true
  showTrackPicker.value = false
}

function showDock() {
  if (hideTimeout) {
    clearTimeout(hideTimeout)
    hideTimeout = null
  }
  isActive.value = true
}

function scheduleDockHide() {
  if (isHovered.value) return
  hideTimeout = window.setTimeout(() => {
    isActive.value = false
  }, 2000)
}

function handleMouseMove(e: MouseEvent) {
  if (e.clientY < 40) {
    showDock()
  } else if (!isHovered.value) {
    scheduleDockHide()
  }
}

function onDockEnter() {
  isHovered.value = true
  showDock()
}

function onDockLeave() {
  isHovered.value = false
  scheduleDockHide()
}

function togglePlayback() {
  if (isPlaying.value) {
    pause()
  } else {
    play()
  }
}

function openTextModal() {
  textInputValue.value = storyText.value
  fileName.value = ''
  showTextModal.value = true
}

function handleFileUpload(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  fileName.value = file.name
  const reader = new FileReader()
  reader.onload = (e) => {
    textInputValue.value = e.target?.result as string
  }
  reader.readAsText(file)
}

function loadText() {
  if (!textInputValue.value.trim()) return
  setStoryText(textInputValue.value)
  showTextModal.value = false
  play()
}

function handleTouchStart(e: TouchEvent) {
  const nav = document.querySelector('.dock')
  const toggle = document.querySelector('.dock-toggle')
  if (
    isActive.value &&
    nav && !nav.contains(e.target as Node) &&
    toggle && !toggle.contains(e.target as Node)
  ) {
    isActive.value = false
  }
}

onMounted(() => {
  window.addEventListener('mousemove', handleMouseMove)
  window.addEventListener('touchstart', handleTouchStart, { passive: true })
  isActive.value = true
  scheduleDockHide()
  initAudio()
})

onUnmounted(() => {
  window.removeEventListener('mousemove', handleMouseMove)
  window.removeEventListener('touchstart', handleTouchStart)
  if (hideTimeout) clearTimeout(hideTimeout)
  if (audioElement.value) {
    audioElement.value.pause()
  }
})
</script>

<template>
  <!-- Mobile toggle button -->
  <button class="dock-toggle" @click="isActive = !isActive" aria-label="Toggle menu">
    <span class="dock-toggle-icon">{{ isActive ? '✕' : '☰' }}</span>
  </button>

  <nav
    :class="['dock', { 'dock--active': isActive, 'dock--hovered': isHovered }]"
    @mouseenter="onDockEnter"
    @mouseleave="onDockLeave"
  >
    <RouterLink
      v-for="route in navRoutes"
      :key="route.name"
      :to="route.path"
      class="dock-item"
      active-class="dock-item--active"
      :title="route.label"
    >
      <span class="dock-icon">{{ route.icon }}</span>
      <span class="dock-label">{{ route.label }}</span>
    </RouterLink>

    <button
      class="dock-item music-toggle"
      :title="musicPlaying ? 'Pause Music' : 'Play Music'"
      @click="toggleMusic"
    >
      <span class="dock-icon">{{ musicPlaying ? '🎵' : '🔇' }}</span>
      <span class="dock-label">Music</span>
    </button>

    <button
      class="dock-item"
      title="Choose Track"
      @click="showTrackPicker = !showTrackPicker"
    >
      <span class="dock-icon">🎶</span>
      <span class="dock-label">Tracks</span>
    </button>

    <div v-if="showTrackPicker" class="track-picker">
      <button
        v-for="(track, index) in audioTracks"
        :key="track.file"
        :class="['track-option', { 'track-option--active': index === currentTrackIndex }]"
        @click="selectTrack(index)"
      >
        {{ track.name }}
      </button>
    </div>

    <div class="dock-divider"></div>

    <button class="dock-item" title="Edit Text" @click="openTextModal">
      <span class="dock-icon">📝</span>
      <span class="dock-label">Text</span>
    </button>

    <!-- Reader controls — visible when a story is loaded -->
    <template v-if="storyText">
      <button
        class="dock-item"
        :title="isPlaying ? 'Pause' : 'Play'"
        @click="togglePlayback"
      >
        <span class="dock-icon">{{ isPlaying ? '⏸' : '▶️' }}</span>
        <span class="dock-label">{{ isPlaying ? 'Pause' : 'Play' }}</span>
      </button>
      <button class="dock-item" title="Reset" @click="reset">
        <span class="dock-icon">⏮</span>
        <span class="dock-label">Reset</span>
      </button>
      <div class="dock-item dock-stats" title="Word progress">
        <span class="dock-icon">📊</span>
        <span class="dock-label">{{ currentIndex + 1 }}/{{ words.length }}</span>
      </div>
    </template>
  </nav>

  <!-- Text edit modal -->
  <Teleport to="body">
    <div v-if="showTextModal" class="text-modal-overlay" @click.self="showTextModal = false">
      <div class="text-modal">
        <h2>Enter Text</h2>

        <label class="modal-file-upload">
          <input type="file" accept=".txt,.md" @change="handleFileUpload" />
          <span class="modal-upload-btn">Choose File</span>
          <span v-if="fileName" class="modal-file-name">{{ fileName }}</span>
        </label>

        <div class="modal-divider">or</div>

        <textarea
          v-model="textInputValue"
          placeholder="Paste your text here..."
          class="modal-textarea"
          rows="10"
        ></textarea>

        <div class="modal-actions">
          <button
            class="modal-btn modal-btn--primary"
            :disabled="!textInputValue.trim()"
            @click="loadText"
          >
            Start Reading
          </button>
          <button class="modal-btn" @click="showTextModal = false">Close</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
/* Mobile toggle button */
.dock-toggle {
  display: none;
  position: fixed;
  top: 0.5rem;
  right: 0.5rem;
  z-index: 1001;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 0.5rem;
  color: #e2e8f0;
  width: 2.5rem;
  height: 2.5rem;
  cursor: pointer;
  align-items: center;
  justify-content: center;
}

.dock-toggle-icon {
  font-size: 1.25rem;
}

.dock {
  position: fixed;
  left: 0;
  right: 0;
  top: 0;
  transform: translateY(calc(-100% + 6px));
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.25rem;
  padding: 0.4rem 0.75rem;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(10px);
  border-radius: 0 0 0.75rem 0.75rem;
  z-index: 1000;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.dock--active {
  transform: translateY(0);
}

.dock-item {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  color: #94a3b8;
  text-decoration: none;
  padding: 0.35rem 0.5rem;
  border-radius: 0.5rem;
  font-size: 0.8rem;
  transition: all 0.2s ease;
  background: transparent;
  border: none;
  cursor: pointer;
  white-space: nowrap;
}

.dock-item:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.dock-icon {
  font-size: 1.1rem;
  min-width: 1.25rem;
  text-align: center;
}

.dock-label {
  opacity: 0;
  max-width: 0;
  overflow: hidden;
  transition: all 0.2s ease;
}

.dock--hovered .dock-label {
  opacity: 1;
  max-width: 100px;
}

.dock-item:hover {
  color: #e2e8f0;
  background-color: rgba(255, 255, 255, 0.1);
}

.dock-item--active {
  color: #e2e8f0;
  background-color: rgba(100, 100, 255, 0.3);
}

.music-toggle {
  margin-left: 0.25rem;
  border-left: 1px solid rgba(255, 255, 255, 0.1);
  padding-left: 0.5rem;
}

.dock-divider {
  width: 1px;
  height: 1.5rem;
  background: rgba(255, 255, 255, 0.1);
  margin: 0 0.15rem;
}

.dock-stats {
  cursor: default;
  font-size: 0.75rem;
  color: #64748b;
}

.track-picker {
  position: absolute;
  top: calc(100% + 0.5rem);
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.9);
  backdrop-filter: blur(10px);
  border-radius: 0.75rem;
  padding: 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  min-width: 160px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.track-option {
  background: transparent;
  border: none;
  color: #94a3b8;
  padding: 0.5rem 0.75rem;
  border-radius: 0.5rem;
  cursor: pointer;
  text-align: left;
  font-size: 0.8rem;
  font-family: inherit;
  white-space: nowrap;
  transition: all 0.2s ease;
}

.track-option:hover {
  color: #e2e8f0;
  background-color: rgba(255, 255, 255, 0.1);
}

.track-option--active {
  color: #e2e8f0;
  background-color: rgba(99, 102, 241, 0.3);
}

@media (max-width: 768px) {
  .dock-toggle {
    display: flex;
  }

  .dock {
    transform: translateY(-100%);
    flex-direction: column;
    align-items: stretch;
    padding: 0.75rem;
    padding-top: 3rem;
    border-radius: 0 0 1rem 1rem;
  }

  .dock--active {
    transform: translateY(0);
  }

  .dock-label {
    opacity: 1;
    max-width: 100px;
  }

  .dock-divider {
    width: 100%;
    height: 1px;
    margin: 0.25rem 0;
  }

  .music-toggle {
    margin-left: 0;
    border-left: none;
    padding-left: 0.5rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    padding-top: 0.5rem;
  }

  .track-picker {
    position: static;
    transform: none;
    margin-top: 0.25rem;
    margin-left: 1.5rem;
  }
}

/* Text edit modal */
.text-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(4px);
}

.text-modal {
  background: rgba(20, 20, 40, 0.95);
  padding: 2rem;
  border-radius: 1rem;
  border: 1px solid rgba(100, 100, 255, 0.3);
  max-width: 600px;
  width: 90%;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.text-modal h2 {
  color: #e2e8f0;
  font-size: 1.25rem;
  margin: 0;
}

.modal-file-upload {
  display: flex;
  align-items: center;
  gap: 1rem;
  cursor: pointer;
}

.modal-file-upload input {
  display: none;
}

.modal-upload-btn {
  background-color: #374151;
  color: #e2e8f0;
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  transition: background-color 0.2s;
}

.modal-upload-btn:hover {
  background-color: #4b5563;
}

.modal-file-name {
  color: #94a3b8;
  font-size: 0.875rem;
}

.modal-divider {
  color: #64748b;
  font-size: 0.875rem;
  text-align: center;
}

.modal-textarea {
  width: 100%;
  padding: 1rem;
  background: rgba(30, 30, 50, 0.9);
  border: 1px solid rgba(100, 100, 255, 0.3);
  color: #e2e8f0;
  border-radius: 0.5rem;
  font-family: inherit;
  font-size: 1rem;
  resize: vertical;
}

.modal-textarea::placeholder {
  color: #64748b;
}

.modal-textarea:focus {
  outline: none;
  border-color: #6366f1;
}

.modal-actions {
  display: flex;
  gap: 0.75rem;
}

.modal-btn {
  background: #374151;
  border: none;
  color: #e2e8f0;
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  cursor: pointer;
  font-family: inherit;
  font-size: 0.9rem;
  transition: background-color 0.2s;
}

.modal-btn:hover {
  background: #4b5563;
}

.modal-btn--primary {
  background: #6366f1;
}

.modal-btn--primary:hover:not(:disabled) {
  background: #4f46e5;
}

.modal-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
