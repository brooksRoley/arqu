<template>
  <div class="relative w-full h-screen bg-black overflow-hidden">
    <!-- Layer 0: Liquid Glass — ripples, particles, glass sphere cursor -->
    <iframe src="/liquid-glass.html" class="full-frame" />

    <!-- Layer 1: Vibe Transmission — binaural drawing canvas (mix-blend-screen) -->
    <VibeTransmission />
  </div>
</template>

<script setup lang="ts">
import VibeTransmission from '@/components/VibeTransmission.vue'
</script>

<style scoped>
.full-frame {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border: none;
  z-index: 0;
}
</style>
