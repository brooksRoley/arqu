<script setup lang="ts">
import { ref, computed, watch } from 'vue'
const URL = window.URL
import { useJournalStore } from '@/composables/useJournalStore'
import { useTTS } from '@/composables/useTTS'
import { useStoryStore } from '@/composables/useStoryStore'
import { usePollStore } from '@/composables/usePollStore'
import JournalCanvas from '@/components/JournalCanvas.vue'
import JournalRecorder from '@/components/JournalRecorder.vue'

const {
  sortedEntries,
  activeEntry,
  todayEntries,
  createEntry,
  updateEntryText,
  setMood,
  addDrawing,
  addAudioClip,
  deleteEntry,
  setActiveEntry,
  synthesizeToday,
  getEntryTextForStoryStore,
} = useJournalStore()

const { speak, toggle, isSpeaking, isPaused, stop: stopTTS, progress: ttsProgress, supported: ttsSupported } = useTTS()
const { setStoryText } = useStoryStore()
const { token: pollToken } = usePollStore()

// ── UI State ───────────────────────────────────────────────────────

type ActiveTab = 'write' | 'draw' | 'listen'
const tab = ref<ActiveTab>('write')
const showHistory = ref(false)

const accentColor = computed(() => pollToken.value?.palette.accent || '#a78bfa')

// Auto-create an entry if none active
if (!activeEntry.value) {
  createEntry()
}

// ── Text editing ───────────────────────────────────────────────────

const textInput = ref(activeEntry.value?.text || '')

watch(activeEntry, (entry) => {
  textInput.value = entry?.text || ''
})

let saveTimeout: ReturnType<typeof setTimeout> | null = null
function onTextInput() {
  if (!activeEntry.value) return
  if (saveTimeout) clearTimeout(saveTimeout)
  saveTimeout = setTimeout(() => {
    updateEntryText(activeEntry.value!.id, textInput.value)
  }, 400)
}

// ── Mood chips ─────────────────────────────────────────────────────

const moods = ['calm', 'anxious', 'hopeful', 'scattered', 'focused', 'grateful', 'heavy', 'energized']

function toggleMood(mood: string) {
  if (!activeEntry.value) return
  setMood(activeEntry.value.id, activeEntry.value.mood === mood ? null : mood)
}

// ── Drawing ────────────────────────────────────────────────────────

function onDrawingSaved(dataUrl: string) {
  if (!activeEntry.value) return
  addDrawing(activeEntry.value.id, dataUrl)
}

// ── Audio ──────────────────────────────────────────────────────────

function onRecorded(blob: Blob, duration: number) {
  if (!activeEntry.value) return
  addAudioClip(activeEntry.value.id, blob, duration)
}

// ── TTS ────────────────────────────────────────────────────────────

function readAloud() {
  if (!activeEntry.value?.text) return
  toggle(activeEntry.value.text)
}

// ── Feed into trance / zeromind ────────────────────────────────────

function sendToZeromind() {
  if (!activeEntry.value) return
  const text = getEntryTextForStoryStore(activeEntry.value.id)
  if (text) setStoryText(text)
}

// ── Synthesis ──────────────────────────────────────────────────────

const latestSynthesis = ref<ReturnType<typeof synthesizeToday> | null>(null)

function runSynthesis() {
  latestSynthesis.value = synthesizeToday()
}

// ── New entry ──────────────────────────────────────────────────────

function newEntry() {
  createEntry()
  tab.value = 'write'
  textInput.value = ''
}

// ── Date formatting ────────────────────────────────────────────────

function formatTime(ts: number): string {
  return new Date(ts).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
}

function formatDate(ts: number): string {
  return new Date(ts).toLocaleDateString([], { month: 'short', day: 'numeric' })
}
</script>

<template>
  <div class="journal-wrap">
    <div class="journal-header">
      <div class="header-left">
        <h1 class="journal-title">Journal</h1>
        <span class="entry-count">{{ todayEntries.length }} today</span>
      </div>
      <div class="header-actions">
        <button class="action-btn" @click="showHistory = !showHistory">
          {{ showHistory ? 'Close' : 'History' }}
        </button>
        <button class="action-btn action-btn--new" @click="newEntry">+ New</button>
      </div>
    </div>

    <!-- History sidebar -->
    <Transition name="slide-in">
      <div v-if="showHistory" class="history-panel">
        <div
          v-for="entry in sortedEntries"
          :key="entry.id"
          :class="['history-item', { 'history-item--active': entry.id === activeEntry?.id }]"
          @click="setActiveEntry(entry.id); showHistory = false"
        >
          <span class="history-date">{{ formatDate(entry.createdAt) }} {{ formatTime(entry.createdAt) }}</span>
          <span class="history-preview">{{ entry.text.slice(0, 60) || '(empty)' }}{{ entry.text.length > 60 ? '...' : '' }}</span>
          <div class="history-meta">
            <span v-if="entry.mood" class="history-mood">{{ entry.mood }}</span>
            <span v-if="entry.drawings.length" class="history-badge">{{ entry.drawings.length }} drawing{{ entry.drawings.length > 1 ? 's' : '' }}</span>
            <span v-if="entry.audioClips.length" class="history-badge">{{ entry.audioClips.length }} clip{{ entry.audioClips.length > 1 ? 's' : '' }}</span>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Active entry -->
    <div v-if="activeEntry" class="entry-card">
      <!-- Tabs -->
      <div class="tab-bar">
        <button :class="['tab', { 'tab--active': tab === 'write' }]" @click="tab = 'write'">Write</button>
        <button :class="['tab', { 'tab--active': tab === 'draw' }]" @click="tab = 'draw'">Draw</button>
        <button :class="['tab', { 'tab--active': tab === 'listen' }]" @click="tab = 'listen'">Listen</button>
      </div>

      <!-- Write tab -->
      <div v-if="tab === 'write'" class="tab-content">
        <textarea
          v-model="textInput"
          @input="onTextInput"
          class="journal-textarea"
          placeholder="What's on your mind..."
          rows="10"
        />

        <!-- Mood chips -->
        <div class="mood-section">
          <span class="section-label">Mood</span>
          <div class="mood-chips">
            <button
              v-for="m in moods"
              :key="m"
              :class="['mood-chip', { 'mood-chip--active': activeEntry.mood === m }]"
              @click="toggleMood(m)"
            >{{ m }}</button>
          </div>
        </div>

        <!-- Actions -->
        <div class="write-actions">
          <button v-if="ttsSupported" class="action-btn" @click="readAloud">
            {{ isSpeaking ? 'Pause' : isPaused ? 'Resume' : 'Read Aloud' }}
          </button>
          <button class="action-btn" @click="sendToZeromind">Send to Zeromind</button>
          <button class="action-btn action-btn--subtle" @click="deleteEntry(activeEntry!.id)">Delete</button>
        </div>

        <div v-if="isSpeaking || isPaused" class="tts-progress">
          <div class="tts-fill" :style="{ width: `${ttsProgress}%` }" />
        </div>
      </div>

      <!-- Draw tab -->
      <div v-if="tab === 'draw'" class="tab-content">
        <JournalCanvas :accent-color="accentColor" @save="onDrawingSaved" />

        <div v-if="activeEntry.drawings.length" class="saved-drawings">
          <span class="section-label">Saved</span>
          <div class="drawing-grid">
            <img
              v-for="(d, i) in activeEntry.drawings"
              :key="i"
              :src="d.dataUrl"
              class="drawing-thumb"
              :alt="`Drawing ${i + 1}`"
            />
          </div>
        </div>
      </div>

      <!-- Listen tab -->
      <div v-if="tab === 'listen'" class="tab-content">
        <JournalRecorder @recorded="onRecorded" />

        <div v-if="activeEntry.audioClips.length" class="audio-list">
          <span class="section-label">Recordings</span>
          <div v-for="(clip, i) in activeEntry.audioClips" :key="i" class="audio-item">
            <span class="audio-label">Clip {{ i + 1 }}</span>
            <span class="audio-duration">{{ Math.round(clip.duration) }}s</span>
            <audio v-if="clip.blob" :src="URL.createObjectURL(clip.blob)" controls class="audio-player" />
            <span v-else class="audio-note">Audio not available (session-only)</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Synthesis -->
    <div class="synthesis-section">
      <button class="action-btn action-btn--synthesis" @click="runSynthesis">
        Synthesize Today
      </button>

      <div v-if="latestSynthesis" class="synthesis-card">
        <span class="section-label">Today's Synthesis</span>
        <p class="synthesis-summary">{{ latestSynthesis.summary }}</p>
        <div v-if="latestSynthesis.keywords.length" class="keyword-chips">
          <span v-for="kw in latestSynthesis.keywords" :key="kw" class="chip">{{ kw }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.journal-wrap {
  max-width: 700px;
  margin: 0 auto;
  padding: 1rem 0;
}

.journal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.header-left {
  display: flex;
  align-items: baseline;
  gap: 0.75rem;
}

.journal-title {
  font-size: 1.4rem;
  font-weight: 600;
  color: #e2e8f0;
  margin: 0;
}

.entry-count {
  font-size: 0.75rem;
  color: #64748b;
}

.header-actions {
  display: flex;
  gap: 0.5rem;
}

/* ── Entry card ── */
.entry-card {
  background: rgba(20, 20, 40, 0.85);
  border: 1px solid rgba(100, 100, 255, 0.12);
  border-radius: 0.75rem;
  padding: 1.25rem;
  backdrop-filter: blur(12px);
}

/* ── Tabs ── */
.tab-bar {
  display: flex;
  gap: 0.25rem;
  margin-bottom: 1.25rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  padding-bottom: 0.5rem;
}

.tab {
  padding: 0.4rem 0.8rem;
  border: none;
  background: none;
  color: #64748b;
  font-size: 0.85rem;
  font-family: inherit;
  cursor: pointer;
  border-radius: 0.35rem;
  transition: color 0.15s, background 0.15s;
}

.tab:hover {
  color: #94a3b8;
}

.tab--active {
  color: #e2e8f0;
  background: rgba(99, 102, 241, 0.15);
}

.tab-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* ── Textarea ── */
.journal-textarea {
  width: 100%;
  min-height: 200px;
  padding: 1rem;
  border-radius: 0.5rem;
  border: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(0, 0, 0, 0.3);
  color: #e2e8f0;
  font-family: inherit;
  font-size: 0.95rem;
  line-height: 1.7;
  resize: vertical;
  outline: none;
  transition: border-color 0.15s;
}

.journal-textarea:focus {
  border-color: rgba(99, 102, 241, 0.35);
}

.journal-textarea::placeholder {
  color: #475569;
}

/* ── Mood ── */
.mood-section {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.section-label {
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #64748b;
}

.mood-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.mood-chip {
  font-size: 0.75rem;
  padding: 0.2rem 0.55rem;
  border-radius: 1rem;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.04);
  color: #94a3b8;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.15s;
}

.mood-chip:hover {
  background: rgba(99, 102, 241, 0.1);
  border-color: rgba(99, 102, 241, 0.25);
}

.mood-chip--active {
  background: rgba(99, 102, 241, 0.2);
  border-color: rgba(99, 102, 241, 0.5);
  color: #a5b4fc;
}

/* ── Actions ── */
.write-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.action-btn {
  font-size: 0.8rem;
  padding: 0.45rem 0.85rem;
  border-radius: 0.4rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.04);
  color: #94a3b8;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.15s;
}

.action-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #e2e8f0;
}

.action-btn--new {
  border-color: rgba(99, 102, 241, 0.3);
  color: #a5b4fc;
}

.action-btn--new:hover {
  background: rgba(99, 102, 241, 0.15);
}

.action-btn--subtle {
  border-color: transparent;
  color: #475569;
}

.action-btn--subtle:hover {
  color: #f87171;
  border-color: rgba(248, 113, 113, 0.2);
}

.action-btn--synthesis {
  border-color: rgba(99, 102, 241, 0.3);
  color: #a5b4fc;
  width: 100%;
  padding: 0.6rem;
}

/* ── TTS progress ── */
.tts-progress {
  height: 2px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 1px;
  overflow: hidden;
}

.tts-fill {
  height: 100%;
  background: linear-gradient(90deg, #6366f1, #a78bfa);
  transition: width 0.2s;
}

/* ── Drawings ── */
.saved-drawings {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.drawing-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 0.5rem;
}

.drawing-thumb {
  width: 100%;
  border-radius: 0.35rem;
  border: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(0, 0, 0, 0.3);
}

/* ── Audio ── */
.audio-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.audio-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 0.75rem;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 0.4rem;
  flex-wrap: wrap;
}

.audio-label {
  font-size: 0.85rem;
  color: #cbd5e1;
}

.audio-duration {
  font-size: 0.75rem;
  color: #64748b;
}

.audio-player {
  height: 28px;
  flex: 1;
  min-width: 150px;
}

.audio-note {
  font-size: 0.75rem;
  color: #475569;
  font-style: italic;
}

/* ── Synthesis ── */
.synthesis-section {
  margin-top: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.synthesis-card {
  background: rgba(20, 20, 40, 0.7);
  border: 1px solid rgba(100, 100, 255, 0.1);
  border-radius: 0.6rem;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.synthesis-summary {
  font-size: 0.9rem;
  color: #cbd5e1;
  line-height: 1.6;
  margin: 0;
}

.keyword-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.chip {
  font-size: 0.7rem;
  padding: 0.15rem 0.45rem;
  border-radius: 0.25rem;
  background: rgba(99, 102, 241, 0.12);
  border: 1px solid rgba(99, 102, 241, 0.2);
  color: #a5b4fc;
}

/* ── History panel ── */
.history-panel {
  margin-bottom: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  max-height: 300px;
  overflow-y: auto;
}

.history-item {
  padding: 0.6rem 0.85rem;
  border-radius: 0.5rem;
  border: 1px solid rgba(255, 255, 255, 0.04);
  background: rgba(255, 255, 255, 0.02);
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.history-item:hover {
  background: rgba(99, 102, 241, 0.08);
  border-color: rgba(99, 102, 241, 0.2);
}

.history-item--active {
  border-color: rgba(99, 102, 241, 0.35);
  background: rgba(99, 102, 241, 0.1);
}

.history-date {
  font-size: 0.7rem;
  color: #64748b;
}

.history-preview {
  font-size: 0.82rem;
  color: #94a3b8;
}

.history-meta {
  display: flex;
  gap: 0.4rem;
}

.history-mood {
  font-size: 0.65rem;
  color: #a5b4fc;
}

.history-badge {
  font-size: 0.65rem;
  color: #64748b;
}

/* ── Transitions ── */
.slide-in-enter-active,
.slide-in-leave-active {
  transition: all 0.25s ease;
}

.slide-in-enter-from,
.slide-in-leave-to {
  opacity: 0;
  max-height: 0;
  transform: translateY(-8px);
}
</style>
