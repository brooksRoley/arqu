<script setup lang="ts">
import { ref, computed } from 'vue'
import { usePollStore } from '@/composables/usePollStore'
import type { PollAnswers } from '@/composables/usePollStore'

const emit = defineEmits<{ (e: 'done'): void }>()

const { answers, setAnswer, submitPoll, resetPoll } = usePollStore()

const pollStep = ref(1)
const pollDirection = ref<'forward' | 'back'>('forward')

type QuestionOption = { value: string; label: string; sublabel: string }

const questions: Array<{
  key: keyof PollAnswers
  text: string
  options: QuestionOption[]
}> = [
  {
    key: 'q1',
    text: 'Did you often create detailed imaginary worlds or friends, and do you find it easy now to get so lost in a book, movie, or daydream that the real world fades away?',
    options: [
      { value: 'vivid-dreamer', label: 'Absolutely', sublabel: "I've always had a rich inner world" },
      { value: 'balanced-escapist', label: 'Somewhat', sublabel: 'I can get lost but stay anchored' },
      { value: 'grounded-realist', label: 'Not really', sublabel: 'I stay grounded in the present' },
    ],
  },
  {
    key: 'q2',
    text: "Have you ever experienced moments where stressful or unpleasant events caused you to mentally 'check out' or go numb, almost like forgetting they happened in the moment?",
    options: [
      { value: 'frequent-dissociation', label: 'Yes, fairly often', sublabel: "It's how I cope" },
      { value: 'occasional-detachment', label: 'Sometimes', sublabel: 'In particularly intense moments' },
      { value: 'fully-present', label: 'Rarely', sublabel: "I tend to stay present even when it's hard" },
    ],
  },
  {
    key: 'q3',
    text: 'Growing up, were you encouraged to do a lot of pretend play or storytelling, and how does that influence how you handle creative or relaxing activities?',
    options: [
      { value: 'creative-storyteller', label: 'Very much so', sublabel: 'Creativity is central to how I relax' },
      { value: 'structured-play', label: 'Some', sublabel: 'I blend structured and imaginative approaches' },
      { value: 'independent-explorer', label: 'Not much', sublabel: 'I tend toward more pragmatic approaches' },
    ],
  },
  {
    key: 'q4',
    text: 'Do you sometimes find your mind going completely blank during routine tasks or conversations, rather than filling with vivid thoughts or stories?',
    options: [
      { value: 'blank-slate', label: 'Yes, often', sublabel: 'I zone out into a kind of mental static' },
      { value: 'thought-rich', label: "No — my mind's usually active", sublabel: 'Filled with thoughts or imagery' },
      { value: 'context-dependent', label: 'It depends', sublabel: 'Varies a lot by context' },
    ],
  },
]

const currentQuestion = computed(() => questions[pollStep.value - 1])
const pollProgress = computed(() => Math.min((pollStep.value - 1) / questions.length, 1))

function selectAnswer(value: string) {
  const q = currentQuestion.value
  setAnswer(q.key, value as PollAnswers[typeof q.key])
  if (pollStep.value < questions.length) {
    pollDirection.value = 'forward'
    pollStep.value++
  } else {
    submitPoll()
    pollStep.value = 1
    emit('done')
  }
}

function pollBack() {
  if (pollStep.value <= 1) {
    emit('done')
    return
  }
  pollDirection.value = 'back'
  pollStep.value--
}

defineExpose({ resetPoll, pollStep, pollDirection })
</script>

<template>
  <div class="poll-section">
    <Transition
      :name="pollDirection === 'forward' ? 'slide-fwd' : 'slide-back'"
      mode="out-in"
    >
      <div :key="pollStep" class="poll-step">
        <div class="poll-progress">
          <div class="poll-progress-fill" :style="{ width: `${pollProgress * 100}%` }"></div>
        </div>

        <p class="poll-step-label">{{ pollStep }} / {{ questions.length }}</p>
        <p class="poll-question">{{ currentQuestion.text }}</p>

        <div class="poll-options">
          <button
            v-for="opt in currentQuestion.options"
            :key="opt.value"
            :class="[
              'poll-option',
              { 'poll-option--selected': answers[currentQuestion.key] === opt.value },
            ]"
            @click="selectAnswer(opt.value)"
          >
            <span class="option-label">{{ opt.label }}</span>
            <span class="option-sublabel">{{ opt.sublabel }}</span>
          </button>
        </div>

        <button class="btn-ghost poll-back" @click="pollBack">
          ← {{ pollStep <= 1 ? 'Back to home' : 'Back' }}
        </button>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.poll-section {
  max-width: 600px;
  background: rgba(20, 20, 40, 0.85);
  border: 1px solid rgba(100, 100, 255, 0.18);
  border-radius: 1rem;
  padding: 2.5rem 2rem;
  backdrop-filter: blur(12px);
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.5);
}

.poll-progress {
  height: 2px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 1px;
  margin-bottom: 1.5rem;
  overflow: hidden;
}

.poll-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #6366f1, #a78bfa);
  border-radius: 1px;
  transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.poll-step-label {
  font-size: 0.7rem;
  color: #64748b;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  margin: 0 0 1.25rem;
}

.poll-question {
  font-size: 1.05rem;
  color: #e2e8f0;
  line-height: 1.65;
  margin: 0 0 2rem;
  text-align: left;
}

.poll-options {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.poll-option {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.2rem;
  padding: 1rem 1.25rem;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 0.6rem;
  color: #e2e8f0;
  cursor: pointer;
  font-family: inherit;
  text-align: left;
  transition: background 0.15s, border-color 0.15s, transform 0.1s;
  width: 100%;
}

.poll-option:hover {
  background: rgba(99, 102, 241, 0.12);
  border-color: rgba(99, 102, 241, 0.35);
  transform: translateX(2px);
}

.poll-option--selected {
  background: rgba(99, 102, 241, 0.2);
  border-color: rgba(99, 102, 241, 0.6);
}

.option-label {
  font-size: 0.95rem;
  font-weight: 500;
}

.option-sublabel {
  font-size: 0.78rem;
  color: #94a3b8;
}

.btn-ghost {
  background: none;
  border: none;
  color: #64748b;
  font-size: 0.8rem;
  font-family: inherit;
  cursor: pointer;
  padding: 0.4rem 0;
  transition: color 0.15s;
}

.btn-ghost:hover { color: #94a3b8; }

.poll-back { display: block; }

/* Poll transitions */
.slide-fwd-enter-active,
.slide-fwd-leave-active,
.slide-back-enter-active,
.slide-back-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-fwd-enter-from { opacity: 0; transform: translateX(28px); }
.slide-fwd-leave-to { opacity: 0; transform: translateX(-28px); }
.slide-back-enter-from { opacity: 0; transform: translateX(-28px); }
.slide-back-leave-to { opacity: 0; transform: translateX(28px); }

@media (max-width: 480px) {
  .poll-section { padding: 1.75rem 1.25rem; }
  .poll-question { font-size: 0.95rem; }
  .poll-option { padding: 0.85rem 1rem; }
}
</style>
