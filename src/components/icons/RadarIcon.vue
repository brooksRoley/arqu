<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 48 48"
    fill="none"
    class="radar-icon"
  >
    <circle cx="24" cy="24" r="20" :stroke="dimColor" stroke-width="1.5" />
    <circle cx="24" cy="24" r="12" :stroke="dimColor" stroke-width="1" />
    <circle cx="24" cy="24" r="4" :stroke="dimColor" stroke-width="0.75" />
    <line
      x1="24" y1="24" x2="24" y2="4"
      :stroke="`url(#radar-grad-${uid})`"
      stroke-width="2"
      stroke-linecap="round"
      class="radar-sweep"
    />
    <circle cx="24" cy="24" r="2" :fill="color" class="radar-center" />
    <defs>
      <linearGradient :id="`radar-grad-${uid}`" x1="24" y1="24" x2="24" y2="4">
        <stop offset="0%" :stop-color="color" stop-opacity="1" />
        <stop offset="100%" :stop-color="color" stop-opacity="0" />
      </linearGradient>
    </defs>
  </svg>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  size?: number
  color?: string
}>(), {
  size: 40,
  color: '#a78bfa',
})

const uid = Math.random().toString(36).slice(2, 8)
const dimColor = '#4b5563'
</script>

<style scoped>
.radar-icon {
  animation: radar-spin 8s linear infinite;
}

.radar-center {
  animation: radar-pulse 2s ease-in-out infinite;
}

@keyframes radar-spin {
  to { transform: rotate(360deg); }
}

@keyframes radar-pulse {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
}
</style>
