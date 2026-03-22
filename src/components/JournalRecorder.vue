<script setup lang="ts">
import { ref, onUnmounted } from 'vue'

const emit = defineEmits<{
  recorded: [blob: Blob, duration: number]
}>()

const isRecording = ref(false)
const recordingDuration = ref(0)
const hasPermission = ref<boolean | null>(null)

let mediaRecorder: MediaRecorder | null = null
let chunks: BlobPart[] = []
let startTime = 0
let durationTimer: ReturnType<typeof setInterval> | null = null

async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    hasPermission.value = true

    mediaRecorder = new MediaRecorder(stream, {
      mimeType: MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : 'audio/webm'
    })

    chunks = []
    startTime = Date.now()
    recordingDuration.value = 0

    durationTimer = setInterval(() => {
      recordingDuration.value = Math.round((Date.now() - startTime) / 1000)
    }, 250)

    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunks.push(e.data)
    }

    mediaRecorder.onstop = () => {
      const blob = new Blob(chunks, { type: mediaRecorder!.mimeType })
      const duration = (Date.now() - startTime) / 1000
      emit('recorded', blob, duration)
      cleanup()
    }

    mediaRecorder.start()
    isRecording.value = true
  } catch {
    hasPermission.value = false
  }
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state === 'recording') {
    mediaRecorder.stop()
    // Stop all tracks to release mic
    mediaRecorder.stream.getTracks().forEach((t) => t.stop())
  }
  isRecording.value = false
}

function cleanup() {
  if (durationTimer) {
    clearInterval(durationTimer)
    durationTimer = null
  }
  mediaRecorder = null
  chunks = []
}

function formatDuration(secs: number): string {
  const m = Math.floor(secs / 60)
  const s = secs % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

onUnmounted(() => {
  if (isRecording.value) stopRecording()
  cleanup()
})
</script>

<template>
  <div class="journal-recorder">
    <button
      v-if="!isRecording"
      class="rec-btn"
      @click="startRecording"
    >
      <span class="rec-dot" />
      Record Audio
    </button>

    <button
      v-else
      class="rec-btn rec-btn--active"
      @click="stopRecording"
    >
      <span class="rec-dot rec-dot--live" />
      {{ formatDuration(recordingDuration) }} — tap to stop
    </button>

    <p v-if="hasPermission === false" class="rec-error">
      Microphone access denied. Check browser permissions.
    </p>
  </div>
</template>

<style scoped>
.journal-recorder {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.rec-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 1rem;
  border-radius: 0.5rem;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.04);
  color: #94a3b8;
  font-family: inherit;
  font-size: 0.85rem;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
  width: fit-content;
}

.rec-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #e2e8f0;
}

.rec-btn--active {
  border-color: rgba(239, 68, 68, 0.5);
  background: rgba(239, 68, 68, 0.1);
  color: #fca5a5;
}

.rec-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #64748b;
  flex-shrink: 0;
}

.rec-dot--live {
  background: #ef4444;
  animation: pulse-dot 1s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.rec-error {
  font-size: 0.78rem;
  color: #f87171;
  margin: 0;
}
</style>
