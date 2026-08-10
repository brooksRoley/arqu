<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAnalytics, type StreakData } from '@/composables/useAnalytics'
import { usePollStore } from '@/composables/usePollStore'

const router = useRouter()
const { fetchStreak } = useAnalytics()
const { token: archetype } = usePollStore()

const streakData = ref<StreakData | null>(null)

// Map poll archetype theme to best-fit trance session
const ARCHETYPE_TRANCE: Record<string, { route: string; label: string; icon: string }> = {
  dreamlike: { route: '/webaudio', label: 'Star Tunnel', icon: '✦' },
  electric:  { route: '/zeromind', label: 'Zeromind',    icon: '🔮' },
  void:      { route: '/spiral',   label: 'Spiral',      icon: '🌀' },
  organic:   { route: '/trance',   label: 'Tone Engine',  icon: '🎧' },
  liminal:   { route: '/zeromind', label: 'Zeromind',    icon: '🔮' },
}

interface PracticeStep {
  route: string
  label: string
  description: string
  icon: string
}

const tranceStep = computed<PracticeStep>(() => {
  const theme = archetype.value?.theme
  const match = theme ? ARCHETYPE_TRANCE[theme] : null
  return match
    ? { route: match.route, label: match.label, description: 'dissolve into signal', icon: match.icon }
    : { route: '/zeromind', label: 'Zeromind', description: 'dissolve into signal', icon: '🔮' }
})

const steps = computed<PracticeStep[]>(() => [
  { route: '/checkin',     label: 'Check-in', description: 'ground in the present', icon: '◐' },
  tranceStep.value,
  { route: '/journal',     label: 'Journal',  description: 'witness what surfaced',  icon: '◎' },
])

// Optional deepening step — binaural entrainment on your own media
const glassStep: PracticeStep = {
  route: '/studio',
  label: 'Glass Studio',
  description: 'go deeper — binaural session',
  icon: '🌡',
}

// today_active is true if the user has logged any session event today
const todayDone = computed(() => streakData.value?.today_active ?? false)

onMounted(async () => {
  streakData.value = await fetchStreak()
})
</script>

<template>
  <div class="practice-block">
    <div class="practice-header">
      <span class="practice-label">Today's Practice</span>
      <span v-if="todayDone" class="practice-done-badge">done today ✓</span>
    </div>

    <div class="practice-steps">
      <button
        v-for="(step, i) in steps"
        :key="step.route"
        class="practice-step"
        :class="{ 'practice-step--done': todayDone }"
        @click="router.push(step.route)"
      >
        <span class="step-icon">{{ step.icon }}</span>
        <span class="step-label">{{ step.label }}</span>
        <span class="step-desc">{{ step.description }}</span>
      </button>
    </div>

    <button class="practice-deepen" @click="router.push(glassStep.route)">
      <span class="deepen-icon">{{ glassStep.icon }}</span>
      <span class="deepen-label">{{ glassStep.label }}</span>
      <span class="deepen-desc">{{ glassStep.description }}</span>
    </button>
  </div>
</template>

<style scoped>
.practice-block {
  width: 100%;
  max-width: 480px;
  margin: 0 auto 1.25rem;
}

.practice-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.55rem;
}

.practice-label {
  font-size: 0.65rem;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: rgba(255,255,255,0.35);
}

.practice-done-badge {
  font-size: 0.6rem;
  letter-spacing: 0.05em;
  color: #84cc16;
  opacity: 0.8;
}

.practice-steps {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.5rem;
}

@media (max-width: 380px) {
  .practice-steps { grid-template-columns: 1fr; }
}

.practice-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.2rem;
  padding: 0.7rem 0.4rem;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.18s ease, border-color 0.18s ease, transform 0.12s ease;
  text-align: center;
}

.practice-step:hover {
  background: rgba(255,255,255,0.08);
  border-color: rgba(255,255,255,0.16);
  transform: translateY(-1px);
}

.practice-step:focus-visible {
  outline: none;
  box-shadow: 0 0 0 2px #84cc16;
}

.practice-step:active {
  transform: translateY(0);
}

.practice-step--done {
  border-color: rgba(132,204,22,0.2);
}

.step-icon {
  font-size: 1.15rem;
  line-height: 1;
}

.step-label {
  font-size: 0.72rem;
  font-weight: 600;
  color: rgba(255,255,255,0.85);
  letter-spacing: 0.02em;
}

.step-desc {
  font-size: 0.58rem;
  color: rgba(255,255,255,0.35);
  letter-spacing: 0.03em;
}

.practice-deepen {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
  margin-top: 0.5rem;
  padding: 0.55rem 0.8rem;
  background: rgba(16,185,129,0.05);
  border: 1px solid rgba(16,185,129,0.18);
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.18s ease, border-color 0.18s ease, transform 0.12s ease;
  text-align: left;
}

.practice-deepen:hover {
  background: rgba(16,185,129,0.1);
  border-color: rgba(16,185,129,0.32);
  transform: translateY(-1px);
}

.practice-deepen:focus-visible {
  outline: none;
  box-shadow: 0 0 0 2px #10b981;
}

.practice-deepen:active {
  transform: translateY(0);
}

.deepen-icon {
  font-size: 1rem;
  line-height: 1;
}

.deepen-label {
  font-size: 0.72rem;
  font-weight: 600;
  color: rgba(255,255,255,0.85);
  letter-spacing: 0.02em;
}

.deepen-desc {
  font-size: 0.58rem;
  color: rgba(16,185,129,0.7);
  letter-spacing: 0.03em;
  margin-left: auto;
}
</style>
