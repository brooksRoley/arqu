<script setup lang="ts">
import { RouterLink } from 'vue-router'

interface Session {
  title: string
  path: string
  description: string
}

interface Group {
  label: string
  sessions: Session[]
}

const groups: Group[] = [
  {
    label: 'Reading & Narrative',
    sessions: [
      {
        title: 'Reader',
        path: '/reader',
        description: 'Phrase-paced text reader for guided focus and suggestion.'
      },
      {
        title: 'Hypno',
        path: '/hypno',
        description: 'Hypnotic text presentation paired with rhythmic visuals.'
      }
    ]
  },
  {
    label: 'Sound & Entrainment',
    sessions: [
      {
        title: 'Audio',
        path: '/audio',
        description: 'Layered ambient mixer for background entrainment.'
      },
      {
        title: 'WebAudio',
        path: '/webaudio',
        description: 'Full visual binaural session with raw Web Audio engine.'
      },
      {
        title: 'Trance',
        path: '/trance',
        description: 'Guided binaural journey with phase-driven coherence.'
      }
    ]
  },
  {
    label: 'Visual',
    sessions: [
      {
        title: 'Liquid Glass',
        path: '/glass',
        description: 'Refractive moving-glass visual field for soft focus.'
      },
      {
        title: 'Song Sandbox',
        path: '/liquidglass',
        description: 'Glass visuals reactive to your own audio source.'
      },
      {
        title: 'Spiral',
        path: '/spiral',
        description: 'Slow spiral induction loop for fixated attention.'
      },
      {
        title: 'ZeroMind',
        path: '/zeromind',
        description: 'Star tunnel visualization for dreamlike absorption.'
      }
    ]
  }
]
</script>

<template>
  <main class="sessions">
    <header class="sessions-head">
      <h1>Sessions</h1>
      <p class="lede">Pick a tool. Each session is one route into Enfractionation.</p>
    </header>

    <section v-for="group in groups" :key="group.label" class="group">
      <h2 class="group-label">{{ group.label }}</h2>
      <div class="grid">
        <RouterLink
          v-for="s in group.sessions"
          :key="s.path"
          :to="s.path"
          class="card"
        >
          <h3 class="card-title">{{ s.title }}</h3>
          <p class="card-desc">{{ s.description }}</p>
          <span class="card-cta">Open</span>
        </RouterLink>
      </div>
    </section>
  </main>
</template>

<style scoped>
.sessions {
  min-height: 100vh;
  background: #1a1a1a;
  color: #e2e8f0;
  padding: 3rem 1.25rem 4rem;
  max-width: 1080px;
  margin: 0 auto;
  font-family: inherit;
}

.sessions-head {
  margin-bottom: 2.5rem;
}

.sessions-head h1 {
  font-size: 2rem;
  font-weight: 500;
  margin: 0 0 0.5rem;
  letter-spacing: 0.01em;
}

.lede {
  margin: 0;
  color: #94a3b8;
  font-size: 0.95rem;
  line-height: 1.6;
}

.group {
  margin-bottom: 2.5rem;
}

.group-label {
  font-size: 0.7rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: #64748b;
  margin: 0 0 1rem;
}

.grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.75rem;
}

.card {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  padding: 1.1rem 1.25rem;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 0.6rem;
  text-decoration: none;
  color: inherit;
  transition: border-color 0.15s ease, background 0.15s ease;
}

.card:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.18);
}

.card-title {
  margin: 0;
  font-size: 1rem;
  font-weight: 500;
  color: #e2e8f0;
}

.card-desc {
  margin: 0;
  color: #94a3b8;
  font-size: 0.85rem;
  line-height: 1.5;
}

.card-cta {
  margin-top: 0.25rem;
  font-size: 0.7rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #64748b;
}

@media (min-width: 720px) {
  .grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 1rem;
  }
}

@media (min-width: 1000px) {
  .grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}
</style>
