<script setup lang="ts">
import { computed, ref, watch, onMounted, onUnmounted } from 'vue'
import { RouterLink, useRouter, useRoute } from 'vue-router'
import { useStoryStore } from '@/composables/useStoryStore'
import { useTranceEngine } from '@/composables/useTranceEngine'
import { useAuthStore } from '@/composables/useAuthStore'

const router = useRouter()
const route = useRoute()
const {
  storyText,
  words,
  currentIndex,
  isPlaying,
  setStoryText,
  play,
  pause,
  reset,
  backgroundMedia,
  isBackgroundVideo,
  setBackgroundMedia,
  clearBackgroundMedia
} = useStoryStore()

const {
  sessionActive: tranceSessionActive,
  phase: trancePhase,
  coherenceScore: tranceCoherence,
  baselineModulatorActive: tranceBaselineActive,
  ptosisInducerActive: trancePtosisActive,
  avSyncActive: tranceAVActive,
  phaseAccent: tranceAccent,
  startSession: tranceStart,
  stopSession: tranceStop,
  windDown: tranceWindDown,
  toggleBaselineModulator: tranceToggleBaseline,
  togglePtosisInducer: tranceTogglePtosis,
  toggleAVSync: tranceToggleAV
} = useTranceEngine()

const { isAuthenticated, user, logout } = useAuthStore()

function handleLogout() {
  logout()
  menuOpen.value = false
  router.push('/')
}

// Panel toggle
const menuOpen = ref(false)

// Fullbleed detection — auto-minimize on immersive routes
const isFullBleed = computed(() => {
  return ['reader', 'zeromind', 'glass', 'spiral', 'trance', 'webaudio'].includes(
    route.name as string
  )
})

// Auto-hide navbar on fullbleed routes; show on mouse/touch activity
const navVisible = ref(true)
const isFullscreen = ref(false)
let hideNavTimer: ReturnType<typeof setTimeout> | null = null

function showNav() {
  if (!navVisible.value) navVisible.value = true
  if (!isFullBleed.value) return
  if (hideNavTimer) clearTimeout(hideNavTimer)
  if (menuOpen.value) return
  hideNavTimer = setTimeout(() => {
    navVisible.value = false
  }, 3000)
}

function toggleFullscreen() {
  const el = document.documentElement
  if (!document.fullscreenElement && !(document as any).webkitFullscreenElement) {
    if (el.requestFullscreen) el.requestFullscreen()
    else if ((el as any).webkitRequestFullscreen) (el as any).webkitRequestFullscreen()
  } else {
    if (document.exitFullscreen) document.exitFullscreen()
    else if ((document as any).webkitExitFullscreen) (document as any).webkitExitFullscreen()
  }
}

function handleFullscreenChange() {
  isFullscreen.value = !!(document.fullscreenElement || (document as any).webkitFullscreenElement)
}

// Close panel on route change
watch(
  () => route.path,
  () => {
    menuOpen.value = false
  }
)

// Start/stop auto-hide when entering/leaving fullbleed routes
watch(
  isFullBleed,
  (val) => {
    if (val) {
      showNav()
    } else {
      navVisible.value = true
      if (hideNavTimer) {
        clearTimeout(hideNavTimer)
        hideNavTimer = null
      }
    }
  },
  { immediate: true }
)

// While menu is open, keep nav visible; restart timer when closed
watch(menuOpen, (val) => {
  if (!isFullBleed.value) return
  if (val) {
    if (hideNavTimer) {
      clearTimeout(hideNavTimer)
      hideNavTimer = null
    }
    navVisible.value = true
  } else {
    showNav()
  }
})

// Text edit modal state
const showTextModal = ref(false)
const textInputValue = ref('')
const fileName = ref('')

// Background modal state
const showBgModal = ref(false)

// Routes hidden from the main nav bar
const hiddenRoutes = new Set([
  'zeromind', 'spiral', 'trance', 'webaudio', 'fitting', 'poll',
  'login', 'google-callback', 'x-callback',
])

const navRoutes = computed(() => {
  return router
    .getRoutes()
    .filter((route) => route.name && route.path !== '/:pathMatch(.*)*' && !hiddenRoutes.has(route.name as string))
    .map((route) => ({
      name: route.name as string,
      path: route.path,
      label: formatRouteName(route.name as string),
      icon: getRouteIcon(route.name as string)
    }))
})

function formatRouteName(name: string): string {
  const labels: Record<string, string> = {
    glass: 'Liquid Glass',
    poll: 'Discover'
  }
  if (labels[name]) return labels[name]
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
    audio: '🎵',
    glass: '💧',
    spiral: '🌀',
    trance: '🎧',
    poll: '✦'
  }
  return icons[name] || '📄'
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
  menuOpen.value = false
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

function handleBgUpload(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  const url = URL.createObjectURL(file)
  setBackgroundMedia(url, file.type.startsWith('video/'))
  showBgModal.value = false
}

function loadText() {
  if (!textInputValue.value.trim()) return
  setStoryText(textInputValue.value)
  showTextModal.value = false
  play()
}

function openBgModal() {
  showBgModal.value = true
  menuOpen.value = false
}

// Close panel on outside click
function handleOutsideClick(e: MouseEvent) {
  if (!menuOpen.value) return
  const nav = document.querySelector('.navbar')
  if (nav && !nav.contains(e.target as Node)) {
    menuOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleOutsideClick)
  window.addEventListener('mousemove', showNav)
  window.addEventListener('touchstart', showNav, { passive: true })
  document.addEventListener('fullscreenchange', handleFullscreenChange)
  document.addEventListener('webkitfullscreenchange', handleFullscreenChange)
})

onUnmounted(() => {
  document.removeEventListener('click', handleOutsideClick)
  window.removeEventListener('mousemove', showNav)
  window.removeEventListener('touchstart', showNav)
  document.removeEventListener('fullscreenchange', handleFullscreenChange)
  document.removeEventListener('webkitfullscreenchange', handleFullscreenChange)
  if (hideNavTimer) clearTimeout(hideNavTimer)
})
</script>

<template>
  <nav
    :class="[
      'navbar',
      {
        'navbar--floating': isFullBleed,
        'navbar--open': menuOpen,
        'navbar--hidden': isFullBleed && !navVisible
      }
    ]"
  >
    <!-- Collapsed: just the hamburger button -->
    <div class="navbar-top">
      <div v-if="!isFullBleed || menuOpen" class="nav-links">
        <RouterLink
          v-for="r in navRoutes"
          :key="r.name"
          :to="r.path"
          class="nav-link"
          active-class="nav-link--active"
        >
          <span class="nav-link-icon">{{ r.icon }}</span>
          <span class="nav-link-label">{{ r.label }}</span>
        </RouterLink>
      </div>

      <button
        v-if="isFullBleed"
        :class="['fullscreen-btn', { 'fullscreen-btn--floating': !menuOpen }]"
        @click="toggleFullscreen"
        :aria-label="isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'"
      >
        <svg
          v-if="!isFullscreen"
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <polyline points="15 3 21 3 21 9"></polyline>
          <polyline points="9 21 3 21 3 15"></polyline>
          <line x1="21" y1="3" x2="14" y2="10"></line>
          <line x1="3" y1="21" x2="10" y2="14"></line>
        </svg>
        <svg
          v-else
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <polyline points="4 14 10 14 10 20"></polyline>
          <polyline points="20 10 14 10 14 4"></polyline>
          <line x1="10" y1="14" x2="3" y2="21"></line>
          <line x1="21" y1="3" x2="14" y2="10"></line>
        </svg>
      </button>

      <button
        :class="['menu-btn', { 'menu-btn--floating': isFullBleed && !menuOpen }]"
        @click="menuOpen = !menuOpen"
        aria-label="Toggle controls"
      >
        <span class="hamburger-lines" :class="{ 'hamburger-lines--open': menuOpen }">
          <span class="hamburger-line"></span>
          <span class="hamburger-line"></span>
          <span class="hamburger-line"></span>
        </span>
      </button>
    </div>

    <transition name="panel">
      <div v-if="menuOpen" class="navbar-panel">
        <!-- Tools -->
        <div class="panel-section">
          <span class="section-label">Tools</span>
          <div class="section-row">
            <button class="panel-btn" @click="openTextModal">📝 Edit Text</button>
            <button class="panel-btn" @click="openBgModal">🖼️ Background</button>
          </div>
        </div>

        <!-- Trance Engine -->
        <div class="panel-section">
          <span class="section-label" :style="tranceSessionActive ? { color: tranceAccent } : {}">Trance</span>
          <div class="section-row">
            <button
              class="panel-btn"
              :class="{ 'panel-btn--active': tranceSessionActive }"
              @click="tranceSessionActive ? tranceStop() : tranceStart()"
            >
              {{ tranceSessionActive ? '&#9632; Stop' : '&#9654; Session' }}
            </button>
            <span v-if="tranceSessionActive" class="panel-stat" :style="{ color: tranceAccent }">
              {{ trancePhase.toUpperCase() }}
              <template v-if="trancePhase === 'coherence'">&middot; {{ tranceCoherence }}%</template>
            </span>
            <button
              v-if="tranceSessionActive && (trancePhase === 'deepen' || trancePhase === 'joy')"
              class="panel-btn"
              @click="tranceWindDown()"
            >
              Wind Down
            </button>
            <button
              class="panel-btn"
              :class="{ 'panel-btn--active': tranceBaselineActive }"
              @click="tranceToggleBaseline()"
            >
              2.4Hz Pulse
            </button>
            <button
              class="panel-btn"
              :class="{ 'panel-btn--active': trancePtosisActive }"
              @click="tranceTogglePtosis()"
            >
              Ptosis
            </button>
            <button
              class="panel-btn"
              :class="{ 'panel-btn--active': tranceAVActive }"
              @click="tranceToggleAV()"
            >
              AV Sync
            </button>
          </div>
        </div>

        <!-- Reader controls (conditional) -->
        <div v-if="storyText" class="panel-section">
          <span class="section-label">Reader</span>
          <div class="section-row">
            <button class="panel-btn" @click="togglePlayback">
              {{ isPlaying ? '⏸ Pause' : '▶ Play' }}
            </button>
            <button class="panel-btn" @click="reset">⏮ Reset</button>
            <span class="panel-stat">{{ currentIndex + 1 }} / {{ words.length }}</span>
          </div>
        </div>

        <!-- Account -->
        <div class="panel-section">
          <span class="section-label">Account</span>
          <div class="section-row">
            <template v-if="isAuthenticated">
              <span class="panel-stat">{{ user?.display_name || user?.email }}</span>
              <button class="panel-btn" @click="handleLogout">Logout</button>
            </template>
            <RouterLink v-else to="/login" class="panel-btn" @click="menuOpen = false">
              Login
            </RouterLink>
          </div>
        </div>
      </div>
    </transition>
  </nav>

  <!-- Touch/click overlay: catches taps on iframe content when navbar is hidden -->
  <Teleport to="body">
    <div
      v-if="isFullBleed && !navVisible"
      class="nav-activity-overlay"
      @touchstart.passive="showNav"
      @click="showNav"
    ></div>
  </Teleport>

  <!-- Text edit modal -->
  <Teleport to="body">
    <div v-if="showTextModal" class="modal-overlay" @click.self="showTextModal = false">
      <div class="modal">
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

  <!-- Background upload modal -->
  <Teleport to="body">
    <div v-if="showBgModal" class="modal-overlay" @click.self="showBgModal = false">
      <div class="modal">
        <h2>Set Background</h2>

        <div v-if="backgroundMedia" class="bg-preview">
          <video
            v-if="isBackgroundVideo"
            :src="backgroundMedia"
            autoplay
            loop
            muted
            playsinline
            class="bg-preview-media"
          ></video>
          <img v-else :src="backgroundMedia" class="bg-preview-media" alt="background preview" />
        </div>

        <label class="modal-file-upload">
          <input type="file" accept="image/gif,video/mp4,video/webm" @change="handleBgUpload" />
          <span class="modal-upload-btn">{{
            backgroundMedia ? 'Change File' : 'Choose File'
          }}</span>
        </label>

        <div class="modal-actions">
          <button
            v-if="backgroundMedia"
            class="modal-btn modal-btn--danger"
            @click="clearBackgroundMedia(), (showBgModal = false)"
          >
            Clear Background
          </button>
          <button class="modal-btn" @click="showBgModal = false">Close</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
/* ── Default sticky bar ── */
.navbar {
  position: sticky;
  top: 0;
  z-index: 1000;
  background: rgba(10, 10, 20, 0.9);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  transition:
    opacity 0.4s ease,
    transform 0.4s ease;
}

.navbar--hidden {
  opacity: 0;
  transform: translateY(-100%);
  pointer-events: none;
}

/* ── Floating mode (fullbleed pages) ── */
.navbar--floating {
  position: fixed;
  top: 0;
  right: 0;
  left: auto;
  background: transparent;
  backdrop-filter: none;
  border-bottom: none;
  pointer-events: none;
}

.navbar--floating .navbar-top {
  justify-content: flex-end;
  padding: 0.75rem;
}

.navbar--floating .menu-btn,
.navbar--floating .nav-links,
.navbar--floating .navbar-panel {
  pointer-events: auto;
}

/* When opened on fullbleed, give the menu a backdrop */
.navbar--floating.navbar--open {
  left: 0;
  background: rgba(10, 10, 20, 0.85);
  backdrop-filter: blur(16px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.navbar--floating.navbar--open .navbar-top {
  justify-content: flex-start;
}

.navbar-top {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0.75rem;
}

/* ── Nav links row ── */
.nav-links {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  flex: 1;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}

.nav-links::-webkit-scrollbar {
  display: none;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.35rem 0.6rem;
  border-radius: 0.4rem;
  color: #94a3b8;
  text-decoration: none;
  font-size: 0.8rem;
  white-space: nowrap;
  transition:
    color 0.15s,
    background-color 0.15s;
}

.nav-link:hover {
  color: #e2e8f0;
  background: rgba(255, 255, 255, 0.08);
}

.nav-link--active {
  color: #e2e8f0;
  background: rgba(99, 102, 241, 0.25);
}

.nav-link-icon {
  font-size: 1rem;
}

.nav-link-label {
  font-size: 0.8rem;
}

/* ── Hamburger button ── */
.menu-btn {
  flex-shrink: 0;
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 0.4rem;
  color: #94a3b8;
  width: 2.25rem;
  height: 2.25rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition:
    color 0.15s,
    border-color 0.15s,
    background 0.15s;
  padding: 0;
}

.menu-btn:hover {
  color: #e2e8f0;
  border-color: rgba(255, 255, 255, 0.25);
}

/* ── Fullscreen button ── */
.fullscreen-btn {
  flex-shrink: 0;
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 0.4rem;
  color: #94a3b8;
  width: 2.25rem;
  height: 2.25rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition:
    color 0.15s,
    border-color 0.15s,
    background 0.15s;
  padding: 0;
}

.fullscreen-btn:hover {
  color: #e2e8f0;
  border-color: rgba(255, 255, 255, 0.25);
}

.fullscreen-btn--floating {
  width: 2.75rem;
  height: 2.75rem;
  border: none;
  background: transparent;
  border-radius: 0.5rem;
  color: rgba(255, 255, 255, 0.6);
}

.fullscreen-btn--floating:hover {
  background: rgba(255, 255, 255, 0.08);
}

/* Floating hamburger — fully transparent, just the lines */
.menu-btn--floating {
  width: 2.75rem;
  height: 2.75rem;
  border: none;
  background: transparent;
  border-radius: 0.5rem;
}

.menu-btn--floating:hover {
  background: rgba(255, 255, 255, 0.08);
}

/* ── Hamburger lines (CSS, not emoji) ── */
.hamburger-lines {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 4px;
  width: 20px;
  height: 20px;
}

.menu-btn--floating .hamburger-lines {
  gap: 5px;
  width: 24px;
  height: 24px;
}

.hamburger-line {
  display: block;
  width: 100%;
  height: 2px;
  background: currentColor;
  border-radius: 1px;
  transition:
    transform 0.25s ease,
    opacity 0.25s ease;
  transform-origin: center;
}

/* X transform when open */
.hamburger-lines--open .hamburger-line:nth-child(1) {
  transform: translateY(6px) rotate(45deg);
}

.hamburger-lines--open .hamburger-line:nth-child(2) {
  opacity: 0;
}

.hamburger-lines--open .hamburger-line:nth-child(3) {
  transform: translateY(-6px) rotate(-45deg);
}

.menu-btn--floating .hamburger-line {
  height: 2px;
  background: rgba(255, 255, 255, 0.6);
  box-shadow: 0 0 6px rgba(255, 255, 255, 0.15);
}

/* ── Expandable panel ── */
.navbar-panel {
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  padding: 0.5rem 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.panel-enter-active,
.panel-leave-active {
  transition: all 0.2s ease;
  overflow: hidden;
}

.panel-enter-from,
.panel-leave-to {
  opacity: 0;
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
}

.panel-enter-to,
.panel-leave-from {
  opacity: 1;
  max-height: 300px;
}

.panel-section {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.section-label {
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.section-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.35rem;
}

.panel-btn {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: #cbd5e1;
  padding: 0.3rem 0.6rem;
  border-radius: 0.35rem;
  font-size: 0.78rem;
  font-family: inherit;
  cursor: pointer;
  white-space: nowrap;
  transition:
    background 0.15s,
    color 0.15s,
    border-color 0.15s;
}

.panel-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #e2e8f0;
}

.panel-btn--active {
  background: rgba(99, 102, 241, 0.25);
  border-color: rgba(99, 102, 241, 0.4);
  color: #e2e8f0;
}

.panel-stat {
  font-size: 0.78rem;
  color: #64748b;
  padding: 0.3rem 0.5rem;
  font-variant-numeric: tabular-nums;
}

/* ── Desktop tweaks ── */
@media (min-width: 769px) {
  .navbar-panel {
    flex-direction: row;
    flex-wrap: wrap;
    gap: 1rem;
  }

  .panel-section {
    flex-direction: row;
    align-items: center;
    gap: 0.5rem;
  }

  .section-label {
    font-size: 0.7rem;
  }

  .panel-section + .panel-section {
    padding-left: 1rem;
    border-left: 1px solid rgba(255, 255, 255, 0.06);
  }
}

/* ── Modals (shared) ── */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(4px);
}

.modal {
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

.modal h2 {
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

.modal-btn--danger {
  background: #991b1b;
  color: #fecaca;
}

.modal-btn--danger:hover {
  background: #b91c1c;
}

.bg-preview {
  border-radius: 0.5rem;
  overflow: hidden;
  max-height: 200px;
}

.bg-preview-media {
  width: 100%;
  max-height: 200px;
  object-fit: contain;
}
</style>

<style>
/* Non-scoped: this element is teleported to <body> */
.nav-activity-overlay {
  position: fixed;
  inset: 0;
  z-index: 999;
  background: transparent;
}
</style>
