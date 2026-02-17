<script setup lang="ts">
const navCards = [
  {
    icon: '📖',
    title: 'Text Stories',
    description: 'Speed-read through uploaded stories and text',
    to: '/reader'
  },
  {
    icon: '🌀',
    title: 'Zeromind',
    description: 'Generative visuals with streaming text',
    to: '/zeromind'
  },
  {
    icon: '🎵',
    title: 'Audio',
    description: 'Browse and play background audio tracks',
    to: '/audio'
  },
  {
    icon: '💧',
    title: 'Resume',
    description: 'Interactive liquid glass resume',
    to: '/resume'
  },
  {
    icon: '🌀',
    title: 'Spiral',
    description: 'Hypnotic spiral with trance words',
    to: '/spiral'
  }
]
</script>

<template>
  <div class="home">
    <h1 class="title">Channel Zero</h1>
    <p class="subtitle">Choose your experience</p>

    <div class="nav-grid">
      <router-link
        v-for="card in navCards"
        :key="card.title"
        :to="card.to"
        class="nav-card"
      >
        <span class="card-icon">{{ card.icon }}</span>
        <span class="card-title">{{ card.title }}</span>
        <span class="card-desc">{{ card.description }}</span>
      </router-link>
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
  margin-top: 2rem;
}

.subtitle {
  font-size: 1rem;
  color: #94a3b8;
  margin-bottom: 2rem;
}

.nav-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.25rem;
  max-width: 600px;
  margin: 0 auto;
}

.nav-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 2rem 1.5rem;
  background: rgba(30, 30, 50, 0.8);
  border: 1px solid rgba(100, 100, 255, 0.15);
  border-radius: 1rem;
  text-decoration: none;
  color: #e2e8f0;
  transition: all 0.25s ease;
}

.nav-card:hover {
  background: rgba(40, 40, 70, 0.9);
  border-color: rgba(99, 102, 241, 0.5);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}

.card-icon {
  font-size: 2.5rem;
}

.card-title {
  font-size: 1.1rem;
  font-weight: 600;
}

.card-desc {
  font-size: 0.8rem;
  color: #94a3b8;
  line-height: 1.4;
}

@media (max-width: 480px) {
  .nav-grid {
    grid-template-columns: 1fr;
  }
}
</style>
