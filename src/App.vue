<script setup lang="ts">
import { computed } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import NavBar from '@/components/NavBar.vue'

const route = useRoute()

const isFullBleed = computed(() => {
  return ['zeromind', 'resume'].includes(route.name as string)
})
</script>

<template>
  <div class="app-container">
    <NavBar />

    <main :class="['app-main', { 'app-main--fullbleed': isFullBleed }]">
      <RouterView />
    </main>

    <footer v-if="!isFullBleed" class="app-footer">
      <p>Channel Zero</p>
    </footer>
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
  padding: 2rem;
  padding-left: 4rem;
  max-width: 900px;
  width: 100%;
  margin: 0 auto;
}

.app-main--fullbleed {
  padding: 0;
  max-width: none;
  position: relative;
}

.app-footer {
  padding: 0.75rem;
  padding-left: 4rem;
  text-align: left;
  font-size: 0.7rem;
  color: #475569;
}

@media (max-width: 768px) {
  .app-main {
    padding: 1rem;
    padding-left: 3rem;
  }
}
</style>
