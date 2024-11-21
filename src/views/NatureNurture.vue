<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useLocalStorage } from '@vueuse/core'

interface Theme {
  name: string
  mainColor: string
  accentColor: string
  backgroundColor: string
  textColor: string
}

const themes: Record<string, Theme> = {
  nature: {
    name: 'Nature',
    mainColor: '#2D5A27',
    accentColor: '#8B4513',
    backgroundColor: '#F4F1DE',
    textColor: '#2D5A27'
  },
  cathedral: {
    name: 'Cathedral',
    mainColor: '#464646',
    accentColor: '#2C1810',
    backgroundColor: '#E6E6E6',
    textColor: '#2C1810'
  }
}

// State management
const currentTheme = useLocalStorage('selected-theme', 'nature')
const txtContent = ref<string>('')
const isLoading = ref(true)
const error = ref<string | null>(null)

// Load text file content
const loadTextContent = async () => {
  isLoading.value = true
  error.value = null
  try {
    const response = await fetch('TheGardenofEchoes.txt')
    if (!response.ok) throw new Error('Failed to load content')
    txtContent.value = await response.text()
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'An error occurred'
  } finally {
    isLoading.value = false
  }
}

// Toggle theme
const toggleTheme = () => {
  currentTheme.value = currentTheme.value === 'nature' ? 'cathedral' : 'nature'
}

// Watch theme changes to update document properties
watch(currentTheme, (newTheme) => {
  document.documentElement.style.setProperty('--main-color', themes[newTheme].mainColor)
  document.documentElement.style.setProperty('--accent-color', themes[newTheme].accentColor)
  document.documentElement.style.setProperty('--background-color', themes[newTheme].backgroundColor)
  document.documentElement.style.setProperty('--text-color', themes[newTheme].textColor)
})

onMounted(() => {
  loadTextContent()
})
</script>

<template>
  <div class="theme-container" :class="currentTheme">
    <!-- Header with theme toggle -->
    <header class="theme-header">
      <h1>{{ themes[currentTheme].name }} Theme</h1>
      <button @click="toggleTheme" class="theme-toggle">
        Switch to {{ currentTheme === 'nature' ? 'Cathedral' : 'Nature' }} Theme
      </button>
    </header>

    <!-- Main content area -->
    <main class="content-area">
      <!-- Theme-specific decorative elements -->
      <div class="theme-elements">
        <div v-if="currentTheme === 'nature'" class="nature-elements">
          <div class="leaf" v-for="n in 5" :key="n"></div>
        </div>
        <div v-else class="cathedral-elements">
          <div class="window" v-for="n in 3" :key="n"></div>
        </div>
      </div>

      <!-- Text content display -->
      <div class="text-content">
        <div v-if="isLoading" class="loading">Loading content...</div>
        <div v-else-if="error" class="error">{{ error }}</div>
        <div v-else class="txt-display">{{ txtContent }}</div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.theme-container {
  min-height: 100vh;
  transition: all 0.5s ease-in-out;
  padding: 1rem;
}

/* Theme-specific styles */
.nature {
  --main-color: #2d5a27;
  --accent-color: #8b4513;
  --background-color: #f4f1de;
  --text-color: #2d5a27;
  background-color: var(--background-color);
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='100' viewBox='0 0 100 100'%3E%3Cpath fill='%232D5A27' fill-opacity='0.1' d='M11 18c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm48 25c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm-43-7c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zm63 31c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zM34 90c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zm56-76c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zM12 86c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm28-65c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm23-11c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm-6 60c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm29 22c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zM32 63c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm57-13c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm-9-21c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM60 91c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM35 41c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM12 60c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2z'%3E%3C/path%3E%3C/svg%3E");
}

.cathedral {
  --main-color: #464646;
  --accent-color: #2c1810;
  --background-color: #e6e6e6;
  --text-color: #2c1810;
  background-color: var(--background-color);
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='100' viewBox='0 0 100 100'%3E%3Cpath fill='%23464646' fill-opacity='0.1' d='M15 0h70l-15 100H30L15 0zm50 0h20l-15 100H50L65 0zM85 0h15l-15 100H70L85 0z'%3E%3C/path%3E%3C/svg%3E");
}

/* Header styles */
.theme-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  margin-bottom: 2rem;
  border-radius: var(--border-radius);
  background-color: rgba(255, 255, 255, 0.9);
}

/* Theme-specific border radius */
.nature .theme-header {
  --border-radius: 1rem;
}

.cathedral .theme-header {
  --border-radius: 0;
  clip-path: polygon(0 0, 100% 0, 95% 100%, 5% 100%);
}

/* Toggle button styles */
.theme-toggle {
  padding: 0.5rem 1rem;
  border: none;
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: bold;
  color: white;
}

.nature .theme-toggle {
  background-color: var(--main-color);
  border-radius: 2rem;
}

.cathedral .theme-toggle {
  background-color: var(--main-color);
  clip-path: polygon(10% 0, 90% 0, 100% 50%, 90% 100%, 10% 100%, 0 50%);
}

/* Content area styles */
.content-area {
  position: relative;
  padding: 2rem;
  margin-top: 2rem;
  background-color: rgba(255, 255, 255, 0.9);
}

.nature .content-area {
  border-radius: 1rem;
}

.cathedral .content-area {
  clip-path: polygon(0 0, 100% 0, 98% 98%, 2% 98%);
}

/* Animations */
@keyframes sway {
  0%,
  100% {
    transform: rotate(-5deg);
  }
  50% {
    transform: rotate(5deg);
  }
}

@keyframes float {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

.nature-elements .leaf {
  position: absolute;
  width: 20px;
  height: 20px;
  background-color: var(--main-color);
  opacity: 0.5;
  border-radius: 50% 0 50% 50%;
  animation: sway 3s ease-in-out infinite;
}

.cathedral-elements .window {
  position: absolute;
  width: 30px;
  height: 60px;
  background-color: var(--accent-color);
  opacity: 0.3;
  clip-path: polygon(20% 0%, 80% 0%, 100% 20%, 100% 80%, 80% 100%, 20% 100%, 0% 80%, 0% 20%);
  animation: float 4s ease-in-out infinite;
}

/* Loading and error states */
.loading,
.error {
  padding: 2rem;
  text-align: center;
  color: var(--text-color);
}

.error {
  color: #ff0000;
}

/* Text content display */
.txt-display {
  padding: 2rem;
  color: var(--text-color);
  line-height: 1.6;
}

/* Responsive design */
@media (max-width: 768px) {
  .theme-header {
    flex-direction: column;
    gap: 1rem;
    text-align: center;
  }

  .content-area {
    padding: 1rem;
  }
}
</style>
