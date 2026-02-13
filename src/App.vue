<script setup lang="ts">
import { computed } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import NavBar from '@/components/NavBar.vue'

const route = useRoute()

const isFullBleed = computed(() => {
  return ['zeromind', 'glass', 'resume'].includes(route.name as string)
})
</script>

<template>
  <div class="app-container">
    <NavBar />

    <main :class="['app-main', { 'app-main--fullbleed': isFullBleed }]">
      <RouterView />
    </main>

  </div>
</template>

<style scoped>
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #1a1a1a;
  color: #e2e8f0;
}

.app-main {
  flex: 1;
  padding: 3.5rem 2rem 4rem;
  max-width: 900px;
  width: 100%;
  margin: 0 auto;
}

.app-main--fullbleed {
  padding: 3rem 0 3.5rem;
  max-width: none;
  position: relative;
}

@media (max-width: 768px) {
  .app-main {
    padding: 3.5rem 1rem 4rem;
  }
}
</style>
