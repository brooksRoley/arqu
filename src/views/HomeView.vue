<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useStoryStore } from '@/composables/useStoryStore'

const router = useRouter()
const { setStoryText } = useStoryStore()
const textContent = ref('')
const fileName = ref('')

const handleFileUpload = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  fileName.value = file.name
  const reader = new FileReader()
  reader.onload = (e) => {
    textContent.value = e.target?.result as string
  }
  reader.readAsText(file)
}

const startReading = () => {
  if (!textContent.value.trim()) return
  setStoryText(textContent.value)
  router.push('/reader')
}
</script>

<template>
  <div class="home">
    <h1 class="title">Speed Reader</h1>
    <p class="subtitle">Upload a text file or paste content to start reading</p>

    <div class="input-section">
      <label class="file-upload">
        <input type="file" accept=".txt,.md" @change="handleFileUpload" />
        <span class="upload-btn">Choose File</span>
        <span v-if="fileName" class="file-name">{{ fileName }}</span>
      </label>

      <div class="divider">or</div>

      <textarea
        v-model="textContent"
        placeholder="Paste your text here..."
        class="text-input"
        rows="10"
      ></textarea>

      <button
        @click="startReading"
        :disabled="!textContent.trim()"
        class="start-btn"
      >
        Start Reading
      </button>
    </div>
  </div>
</template>

<style scoped>
.home {
  text-align: center;
}

.title {
  font-size: 2rem;
  font-weight: bold;
  margin-bottom: 0.5rem;
  color: #e2e8f0;
}

.subtitle {
  font-size: 1rem;
  color: #94a3b8;
  margin-bottom: 2rem;
}

.input-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  max-width: 600px;
  margin: 0 auto;
}

.file-upload {
  display: flex;
  align-items: center;
  gap: 1rem;
  cursor: pointer;
}

.file-upload input {
  display: none;
}

.upload-btn {
  background-color: #374151;
  color: #e2e8f0;
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  transition: background-color 0.2s;
}

.upload-btn:hover {
  background-color: #4b5563;
}

.file-name {
  color: #94a3b8;
  font-size: 0.875rem;
}

.divider {
  color: #64748b;
  font-size: 0.875rem;
}

.text-input {
  width: 100%;
  padding: 1rem;
  background-color: #1f2937;
  border: 1px solid #374151;
  border-radius: 0.5rem;
  color: #e2e8f0;
  font-size: 1rem;
  resize: vertical;
  font-family: inherit;
}

.text-input::placeholder {
  color: #64748b;
}

.text-input:focus {
  outline: none;
  border-color: #6366f1;
}

.start-btn {
  background-color: #6366f1;
  color: white;
  padding: 1rem 2rem;
  border: none;
  border-radius: 0.5rem;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.start-btn:hover:not(:disabled) {
  background-color: #4f46e5;
}

.start-btn:disabled {
  background-color: #374151;
  color: #64748b;
  cursor: not-allowed;
}
</style>
