import { ref, computed, readonly } from 'vue'

export type TutorialStep = 'welcome' | 'oscillator' | 'filter' | 'upload' | 'mantra' | 'complete'

const STORAGE_KEY = 'glass-tutorial-done'

const currentStep = ref<TutorialStep>(
  localStorage.getItem(STORAGE_KEY) ? 'complete' : 'welcome'
)

const isActive = computed(() => currentStep.value !== 'complete')

const STEPS: TutorialStep[] = ['welcome', 'oscillator', 'filter', 'upload', 'mantra', 'complete']

function advance() {
  const idx = STEPS.indexOf(currentStep.value)
  if (idx < STEPS.length - 1) {
    currentStep.value = STEPS[idx + 1]
    if (currentStep.value === 'complete') {
      localStorage.setItem(STORAGE_KEY, '1')
    }
  }
}

function skip() {
  currentStep.value = 'complete'
  localStorage.setItem(STORAGE_KEY, '1')
}

function reset() {
  localStorage.removeItem(STORAGE_KEY)
  currentStep.value = 'welcome'
}

export function useGlassTutorial() {
  return {
    currentStep: readonly(currentStep),
    isActive,
    advance,
    skip,
    reset,
  }
}
