<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 48 48"
    fill="none"
    class="signal-icon"
  >
    <circle cx="24" cy="24" r="6" :fill="color" opacity="0.8" />
    <circle cx="24" cy="24" r="12" :stroke="color" stroke-width="1.5" class="ring ring-1" />
    <circle cx="24" cy="24" r="18" :stroke="color" stroke-width="1" class="ring ring-2" />
  </svg>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  size?: number
  color?: string
}>(), {
  size: 40,
  color: '#a78bfa',
})
</script>

<style scoped>
.ring {
  opacity: 0;
  transform-origin: center;
}

.ring-1 {
  animation: ping-ring 2.5s cubic-bezier(0, 0, 0.2, 1) infinite;
}

.ring-2 {
  animation: ping-ring 2.5s cubic-bezier(0, 0, 0.2, 1) infinite;
  animation-delay: 0.8s;
}

@keyframes ping-ring {
  0% {
    opacity: 0.6;
    r: 6;
  }
  100% {
    opacity: 0;
    r: 22;
  }
}
</style>
