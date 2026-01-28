<script setup lang="ts">
import { RouterView } from 'vue-router'
</script>

<template>
  <div class="app-container">
    <header class="app-header">
      <h1 class="app-title">Channel Zero</h1>
      <p class="app-subtitle">Speed Reader</p>
    </header>

    <main class="app-main">
      <RouterView />
    </main>

    <footer class="app-footer">
      <p>Channel Zero - Text to Voice Story Reader</p>
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

.app-header {
  padding: 1rem 2rem;
  text-align: center;
  background-color: rgba(0, 0, 0, 0.3);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.app-title {
  font-size: 1.5rem;
  font-weight: bold;
  margin: 0;
  color: #e2e8f0;
}

.app-subtitle {
  font-size: 0.875rem;
  color: #94a3b8;
  margin: 0.25rem 0 0 0;
}

.app-main {
  flex: 1;
  padding: 2rem;
  max-width: 900px;
  width: 100%;
  margin: 0 auto;
}

.app-footer {
  padding: 1rem;
  text-align: center;
  background-color: rgba(0, 0, 0, 0.3);
  font-size: 0.75rem;
  color: #64748b;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

@media (max-width: 768px) {
  .app-main {
    padding: 1rem;
  }
}
</style>
