<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/composables/useAuthStore'
import { usePollStore } from '@/composables/usePollStore'

const router = useRouter()
const { user } = useAuthStore()
const { token: pollToken } = usePollStore()

const ONBOARDING_KEY = 'channelzero-onboarding'

interface OnboardingState {
  poll: boolean
  calibrate: boolean
  psychoanalysis: boolean
  intake: boolean
  completed: boolean
}

function loadState(): OnboardingState {
  try {
    const raw = localStorage.getItem(ONBOARDING_KEY)
    if (raw) return JSON.parse(raw)
  } catch { /* ignore */ }
  return { poll: false, calibrate: false, psychoanalysis: false, intake: false, completed: false }
}

function saveState(s: OnboardingState) {
  localStorage.setItem(ONBOARDING_KEY, JSON.stringify(s))
}

const state = ref<OnboardingState>(loadState())

// Auto-detect poll completion from pollStore
onMounted(() => {
  if (pollToken.value && !state.value.poll) {
    state.value.poll = true
    saveState(state.value)
  }
})

interface Step {
  key: keyof Omit<OnboardingState, 'completed'>
  title: string
  description: string
  route: string
  icon: string
}

const steps: Step[] = [
  {
    key: 'poll',
    title: 'Vibe Poll',
    description: 'Four quick questions to discover your experience archetype',
    route: '/poll',
    icon: '✦',
  },
  {
    key: 'calibrate',
    title: 'Connect Services',
    description: 'Link Spotify, Strava, and other peripherals for richer signal',
    route: '/calibrate',
    icon: '🔗',
  },
  {
    key: 'psychoanalysis',
    title: 'Psychoanalysis',
    description: 'Deep personality mapping through guided introspection',
    route: '/psychoanalysis',
    icon: '🧠',
  },
  {
    key: 'intake',
    title: 'Intake',
    description: 'Final vibe calibration before entering the matching engine',
    route: '/intake',
    icon: '🎯',
  },
]

const currentStepIndex = computed(() => {
  for (let i = 0; i < steps.length; i++) {
    if (!state.value[steps[i].key]) return i
  }
  return steps.length
})

const progress = computed(() => {
  const done = steps.filter(s => state.value[s.key]).length
  return done / steps.length
})

function markComplete(key: keyof Omit<OnboardingState, 'completed'>) {
  state.value[key] = true
  saveState(state.value)
}

function goToStep(step: Step) {
  router.push(step.route)
}

function skipStep(step: Step) {
  markComplete(step.key)
}

function finishOnboarding() {
  state.value.completed = true
  saveState(state.value)
  router.push('/game')
}

function skipAll() {
  state.value.completed = true
  saveState(state.value)
  router.push('/')
}
</script>

<template>
  <div class="onboarding">
    <div class="onboarding-container">
      <h1 class="onboarding-title">Welcome{{ user?.display_name ? `, ${user.display_name}` : '' }}</h1>
      <p class="onboarding-subtitle">
        Let's get you calibrated. Complete these steps to unlock the matching engine.
      </p>

      <!-- Progress bar -->
      <div class="progress-track">
        <div class="progress-fill" :style="{ width: `${progress * 100}%` }"></div>
      </div>
      <p class="progress-label">{{ steps.filter(s => state[s.key]).length }} / {{ steps.length }} complete</p>

      <!-- Steps -->
      <div class="steps">
        <div
          v-for="(step, i) in steps"
          :key="step.key"
          :class="[
            'step',
            {
              'step--done': state[step.key],
              'step--current': i === currentStepIndex,
              'step--locked': i > currentStepIndex,
            },
          ]"
        >
          <div class="step-indicator">
            <span v-if="state[step.key]" class="step-check">&#x2713;</span>
            <span v-else class="step-number">{{ i + 1 }}</span>
          </div>
          <div class="step-body">
            <div class="step-header">
              <span class="step-icon">{{ step.icon }}</span>
              <span class="step-title">{{ step.title }}</span>
            </div>
            <p class="step-desc">{{ step.description }}</p>
            <div v-if="i === currentStepIndex && !state[step.key]" class="step-actions">
              <button class="btn-primary" @click="goToStep(step)">Start</button>
              <button class="btn-ghost" @click="skipStep(step)">Skip</button>
            </div>
            <div v-else-if="state[step.key]" class="step-actions">
              <button class="btn-ghost btn-sm" @click="goToStep(step)">Redo</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Bottom actions -->
      <div class="onboarding-footer">
        <button
          v-if="currentStepIndex >= steps.length"
          class="btn-primary btn-lg"
          @click="finishOnboarding"
        >
          Enter the Game
        </button>
        <button class="btn-ghost" @click="skipAll">Skip for now</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.onboarding {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background: radial-gradient(ellipse at 50% 20%, rgba(30, 20, 60, 1), rgba(8, 6, 18, 1) 70%);
  color: #e8e4f0;
}

.onboarding-container {
  max-width: 540px;
  width: 100%;
}

.onboarding-title {
  font-size: 1.8rem;
  font-weight: 300;
  letter-spacing: 0.04em;
  margin-bottom: 0.5rem;
}

.onboarding-subtitle {
  color: rgba(232, 228, 240, 0.6);
  font-size: 0.95rem;
  margin-bottom: 2rem;
  line-height: 1.5;
}

/* Progress */
.progress-track {
  height: 4px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #7c5cbf, #a78bfa);
  border-radius: 2px;
  transition: width 0.4s ease;
}

.progress-label {
  font-size: 0.8rem;
  color: rgba(232, 228, 240, 0.4);
  margin-bottom: 2rem;
}

/* Steps */
.steps {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.step {
  display: flex;
  gap: 1rem;
  padding: 1.25rem;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  transition: all 0.3s ease;
}

.step--current {
  background: rgba(124, 92, 191, 0.08);
  border-color: rgba(124, 92, 191, 0.3);
}

.step--done {
  opacity: 0.6;
}

.step--locked {
  opacity: 0.35;
}

.step-indicator {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 0.85rem;
  font-weight: 600;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.step--done .step-indicator {
  background: rgba(124, 92, 191, 0.3);
  border-color: rgba(124, 92, 191, 0.5);
}

.step--current .step-indicator {
  background: rgba(124, 92, 191, 0.2);
  border-color: rgba(167, 139, 250, 0.6);
  box-shadow: 0 0 12px rgba(167, 139, 250, 0.2);
}

.step-check {
  color: #a78bfa;
}

.step-number {
  color: rgba(232, 228, 240, 0.5);
}

.step-body {
  flex: 1;
  min-width: 0;
}

.step-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
}

.step-icon {
  font-size: 1.1rem;
}

.step-title {
  font-size: 1rem;
  font-weight: 500;
}

.step-desc {
  font-size: 0.85rem;
  color: rgba(232, 228, 240, 0.5);
  line-height: 1.4;
  margin-bottom: 0.75rem;
}

.step-actions {
  display: flex;
  gap: 0.75rem;
}

/* Buttons */
.btn-primary {
  padding: 0.5rem 1.25rem;
  border-radius: 8px;
  background: linear-gradient(135deg, #7c5cbf, #6d48b3);
  color: #fff;
  border: none;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-primary:hover {
  background: linear-gradient(135deg, #8d6dd0, #7c5cbf);
  box-shadow: 0 0 16px rgba(167, 139, 250, 0.3);
}

.btn-primary.btn-lg {
  padding: 0.75rem 2rem;
  font-size: 1rem;
}

.btn-ghost {
  padding: 0.5rem 1rem;
  border-radius: 8px;
  background: transparent;
  color: rgba(232, 228, 240, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.1);
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-ghost:hover {
  border-color: rgba(255, 255, 255, 0.2);
  color: rgba(232, 228, 240, 0.8);
}

.btn-ghost.btn-sm {
  padding: 0.3rem 0.75rem;
  font-size: 0.8rem;
}

/* Footer */
.onboarding-footer {
  margin-top: 2.5rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}
</style>
