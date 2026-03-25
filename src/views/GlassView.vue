<template>
  <div class="relative w-full h-screen bg-black overflow-hidden flex items-center justify-center">
    <!-- Layer 0: Liquid Glass Background -->
    <iframe src="/liquid-glass.html" class="absolute inset-0 w-full h-full border-none z-10 opacity-90" />

    <!-- Split UI layout -->
    <div class="relative z-20 w-full flex flex-col items-center xl:flex-row gap-8 xl:gap-16 p-6 md:p-12 max-w-7xl mx-auto h-full overflow-y-auto">
      
      <!-- Tutorial Column -->
      <div class="flex-1 w-full flex justify-end">
        <ToneTutorial class="max-w-md w-full" />
      </div>

      <!-- Looper Studio Column -->
      <div class="flex-1 w-full flex justify-start">
        <LooperStudio class="max-w-md w-full" />
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import ToneTutorial from '@/components/ToneTutorial.vue'
import LooperStudio from '@/components/LooperStudio.vue'
</script>
