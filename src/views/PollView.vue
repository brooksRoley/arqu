<script setup lang="ts">
import { ref, computed } from 'vue'
import { usePollStore } from '@/composables/usePollStore'
import type { PollAnswers } from '@/composables/usePollStore'

const { answers, token, setAnswer, submitPoll, resetPoll } = usePollStore()

const step = ref(token.value ? 5 : 1)
const direction = ref<'forward' | 'back'>('forward')

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

const currentQuestion = computed(() => questions[step.value - 1])
const progress = computed(() => Math.min((step.value - 1) / questions.length, 1))

function select(value: string) {
  const q = currentQuestion.value
  setAnswer(q.key, value as PollAnswers[typeof q.key])
  if (step.value < questions.length) {
    direction.value = 'forward'
    step.value++
  } else {
    submitPoll()
    direction.value = 'forward'
    step.value = 5
  }
}

function back() {
  if (step.value <= 1) return
  direction.value = 'back'
  step.value--
}

function restart() {
  resetPoll()
  direction.value = 'forward'
  step.value = 1
}

const themeLabels: Record<string, string> = {
  dreamlike: 'Dreamlike',
  electric: 'Electric',
  void: 'The Void',
  organic: 'Organic',
  liminal: 'Liminal',
}

const themeDescriptions: Record<string, string> = {
  dreamlike: 'A rich inner world meets dissociative depth — your mind drifts between vivid reverie and the edges of absence.',
  electric: 'Vivid imagination anchored by presence — your creativity crackles with clarity and forward motion.',
  void: 'Grounded in the external, yet prone to going blank — your attention moves through whitespace and silence.',
  organic: 'Rooted and pragmatic — you engage with the world through texture, craft, and tangible experience.',
  liminal: 'In-between states feel natural — you exist in the threshold, ambient and unhurried.',
}
</script>

<template>
  <div class="poll-wrap">
    <div class="poll-card">
      <Transition :name="step === 5 ? 'slide-up' : direction === 'forward' ? 'slide-fwd' : 'slide-back'" mode="out-in">
        <!-- Results screen -->
        <div v-if="step === 5 && token" key="results" class="results">
          <div class="results-theme" :style="{ '--accent': token.palette.accent, '--primary': token.palette.primary }">
            <div class="theme-badge">{{ themeLabels[token.theme] }}</div>
            <p class="theme-desc">{{ themeDescriptions[token.theme] }}</p>
          </div>

          <div class="results-palette">
            <div class="swatch" :style="{ background: token.palette.background }" title="Background" />
            <div class="swatch" :style="{ background: token.palette.primary }" title="Primary" />
            <div class="swatch" :style="{ background: token.palette.accent }" title="Accent" />
          </div>

          <div class="results-block">
            <span class="block-label">Archetype</span>
            <span class="block-value">{{ token.archetype }}</span>
          </div>

          <div class="results-block">
            <span class="block-label">Tone</span>
            <span class="block-value">{{ token.tone }}</span>
          </div>

          <div class="results-block">
            <span class="block-label">Keywords</span>
            <div class="keyword-chips">
              <span v-for="kw in token.keywords" :key="kw" class="chip">{{ kw }}</span>
            </div>
          </div>

          <details class="adlib-details">
            <summary>API adlib prompt</summary>
            <pre class="adlib-pre">{{ token.adlibPrompt }}</pre>
          </details>

          <button class="btn-ghost" @click="restart">Retake</button>
        </div>

        <!-- Question screen -->
        <div v-else :key="step" class="question-screen">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: `${progress * 100}%` }" />
          </div>

          <p class="step-label">{{ step }} / {{ questions.length }}</p>
          <p class="question-text">{{ currentQuestion.text }}</p>

          <div class="options">
            <button
              v-for="opt in currentQuestion.options"
              :key="opt.value"
              class="option-btn"
              :class="{ 'option-btn--selected': answers[currentQuestion.key] === opt.value }"
              @click="select(opt.value)"
            >
              <span class="option-label">{{ opt.label }}</span>
              <span class="option-sublabel">{{ opt.sublabel }}</span>
            </button>
          </div>

          <button v-if="step > 1" class="btn-ghost back-btn" @click="back">← Back</button>
        </div>
      </Transition>
    </div>
  </div>
</template>

<style scoped>
.poll-wrap {
  min-height: calc(100vh - 3rem);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem 1rem;
}

.poll-card {
  width: 100%;
  max-width: 600px;
  background: rgba(20, 20, 40, 0.85);
  border: 1px solid rgba(100, 100, 255, 0.18);
  border-radius: 1rem;
  padding: 2.5rem 2rem;
  backdrop-filter: blur(12px);
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.5);
  overflow: hidden;
  position: relative;
}

/* ── Progress ── */
.progress-bar {
  height: 2px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 1px;
  margin-bottom: 1.5rem;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #6366f1, #a78bfa);
  border-radius: 1px;
  transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.step-label {
  font-size: 0.7rem;
  color: #64748b;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  margin: 0 0 1.25rem;
}

/* ── Question ── */
.question-text {
  font-size: 1.05rem;
  color: #e2e8f0;
  line-height: 1.65;
  margin: 0 0 2rem;
}

/* ── Options ── */
.options {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.option-btn {
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

.option-btn:hover {
  background: rgba(99, 102, 241, 0.12);
  border-color: rgba(99, 102, 241, 0.35);
  transform: translateX(2px);
}

.option-btn--selected {
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

/* ── Ghost button ── */
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

.btn-ghost:hover {
  color: #94a3b8;
}

.back-btn {
  display: block;
}

/* ── Results ── */
.results {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.results-theme {
  text-align: center;
}

.theme-badge {
  display: inline-block;
  font-size: 1.4rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: var(--accent, #a78bfa);
  margin-bottom: 0.75rem;
}

.theme-desc {
  font-size: 0.9rem;
  color: #94a3b8;
  line-height: 1.6;
  margin: 0;
}

.results-palette {
  display: flex;
  gap: 0.5rem;
  justify-content: center;
}

.swatch {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.12);
}

.results-block {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.block-label {
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: #475569;
}

.block-value {
  font-size: 0.92rem;
  color: #cbd5e1;
}

.keyword-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.chip {
  font-size: 0.75rem;
  padding: 0.2rem 0.55rem;
  border-radius: 0.3rem;
  background: rgba(99, 102, 241, 0.15);
  border: 1px solid rgba(99, 102, 241, 0.25);
  color: #a5b4fc;
}

.adlib-details {
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 0.5rem;
  overflow: hidden;
}

.adlib-details summary {
  padding: 0.6rem 1rem;
  font-size: 0.78rem;
  color: #64748b;
  cursor: pointer;
  user-select: none;
  list-style: none;
  transition: color 0.15s;
}

.adlib-details summary:hover {
  color: #94a3b8;
}

.adlib-pre {
  margin: 0;
  padding: 0.75rem 1rem;
  font-size: 0.78rem;
  color: #94a3b8;
  white-space: pre-wrap;
  line-height: 1.55;
  background: rgba(0, 0, 0, 0.2);
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  font-family: inherit;
}

/* ── Slide transitions ── */
.slide-fwd-enter-active,
.slide-fwd-leave-active,
.slide-back-enter-active,
.slide-back-leave-active,
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-fwd-enter-from {
  opacity: 0;
  transform: translateX(28px);
}
.slide-fwd-leave-to {
  opacity: 0;
  transform: translateX(-28px);
}

.slide-back-enter-from {
  opacity: 0;
  transform: translateX(-28px);
}
.slide-back-leave-to {
  opacity: 0;
  transform: translateX(28px);
}

.slide-up-enter-from {
  opacity: 0;
  transform: translateY(20px);
}
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(-12px);
}

/* ── Mobile ── */
@media (max-width: 480px) {
  .poll-card {
    padding: 1.75rem 1.25rem;
  }

  .question-text {
    font-size: 0.95rem;
  }

  .option-btn {
    padding: 0.85rem 1rem;
  }
}
</style>
