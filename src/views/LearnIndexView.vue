<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import { LEARN_TOPICS, type LearnTopic } from '@/data/learn'

interface PhaseGroup {
  phase: 1 | 2 | 3
  phaseName: string
  topics: LearnTopic[]
}

const phases = computed<PhaseGroup[]>(() => {
  const groups: Record<1 | 2 | 3, PhaseGroup> = {
    1: { phase: 1, phaseName: '', topics: [] },
    2: { phase: 2, phaseName: '', topics: [] },
    3: { phase: 3, phaseName: '', topics: [] },
  }
  for (const topic of LEARN_TOPICS) {
    groups[topic.phase].topics.push(topic)
    groups[topic.phase].phaseName = topic.phaseName
  }
  return [groups[1], groups[2], groups[3]].filter((g) => g.topics.length > 0)
})
</script>

<template>
  <main class="learn-index">
    <header class="hero">
      <h1>Learn</h1>
      <p class="subtitle">A curriculum in three phases</p>
    </header>

    <section
      v-for="group in phases"
      :key="group.phase"
      class="phase"
    >
      <div class="phase-header">
        <span class="phase-num">Phase {{ group.phase }}</span>
        <h2 class="phase-name">{{ group.phaseName }}</h2>
      </div>

      <div class="topic-grid">
        <RouterLink
          v-for="topic in group.topics"
          :key="topic.slug"
          :to="`/learn/${topic.slug}`"
          class="topic-card"
        >
          <h3 class="topic-title">{{ topic.title }}</h3>
          <p class="topic-desc">{{ topic.shortDescription }}</p>
          <span class="topic-cta">Read <span aria-hidden="true">&rarr;</span></span>
        </RouterLink>
      </div>
    </section>
  </main>
</template>

<style scoped>
.learn-index {
  min-height: 100vh;
  background: #1a1a1a;
  color: #e2e8f0;
  padding: 4rem 1.5rem 6rem;
}

.hero {
  max-width: 64rem;
  margin: 0 auto 3.5rem;
  text-align: left;
}

.hero h1 {
  font-size: clamp(2.5rem, 5vw, 3.5rem);
  font-weight: 600;
  margin: 0 0 0.5rem;
  letter-spacing: -0.02em;
}

.subtitle {
  font-size: 1.125rem;
  color: #94a3b8;
  margin: 0;
}

.phase {
  max-width: 64rem;
  margin: 0 auto 4rem;
}

.phase-header {
  display: flex;
  align-items: baseline;
  gap: 0.875rem;
  margin-bottom: 1.5rem;
  padding-bottom: 0.875rem;
  border-bottom: 1px solid #2a2a2a;
}

.phase-num {
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #6366f1;
}

.phase-name {
  font-size: 1.5rem;
  font-weight: 500;
  margin: 0;
  color: #e2e8f0;
}

.topic-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

@media (max-width: 720px) {
  .topic-grid {
    grid-template-columns: 1fr;
  }
}

.topic-card {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
  padding: 1.5rem;
  background: #1f1f1f;
  border: 1px solid #2a2a2a;
  border-radius: 10px;
  text-decoration: none;
  color: inherit;
  transition: border-color 180ms ease, transform 180ms ease, background 180ms ease;
}

.topic-card:hover {
  border-color: #3f3f5a;
  background: #232333;
  transform: translateY(-2px);
}

.topic-title {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0;
  color: #e2e8f0;
}

.topic-desc {
  font-size: 0.9375rem;
  line-height: 1.55;
  color: #94a3b8;
  margin: 0;
  flex: 1;
}

.topic-cta {
  font-size: 0.875rem;
  color: #6366f1;
  font-weight: 500;
  margin-top: 0.25rem;
}
</style>
