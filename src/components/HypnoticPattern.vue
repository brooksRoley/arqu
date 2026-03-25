<template>
  <Teleport to="body">
    <transition name="fade">
      <div
        v-if="store.isActive"
        class="fixed inset-0 z-50 flex items-center justify-center w-screen h-screen overflow-hidden bg-black cursor-none pointer-events-auto"
        @click="store.triggerColorShift"
      >
        <div
          class="absolute w-[200vw] h-[200vw] md:w-[150vw] md:h-[150vw] origin-center"
          :style="{
            background: `repeating-radial-gradient(circle at center, transparent 0, transparent 30px, currentColor 30px, currentColor 60px)`,
            color: store.isColorAltered ? '#10b981' : '#ffffff' /* Tailwind emerald-500 or white */,
            animation: `spin-tunnel ${store.spinDuration} linear infinite`
          }"
          style="filter: blur(3px)"
        ></div>

        <div
          class="absolute inset-0 w-full h-full mix-blend-overlay"
          :class="store.isColorAltered ? 'bg-red-600' : 'bg-black'"
          :style="{ animation: `luminance-pulse ${store.pulseDuration} ease-in-out infinite` }"
        ></div>

        <div
          class="z-10 w-3 h-3 bg-white rounded-full shadow-[0_0_30px_15px_rgba(255,255,255,0.8)]"
        ></div>

        <button
          @click.stop="store.stopSession"
          class="absolute bottom-4 right-4 text-white/20 hover:text-white/50 text-xs tracking-widest uppercase"
        >
          Exit
        </button>
      </div>
    </transition>
  </Teleport>
</template>

<script setup>
import { useHypnosisStore } from '@/stores/useHypnosisStore'

const store = useHypnosisStore()
</script>

<style scoped>
/* Custom Keyframes that Tailwind can't easily handle dynamically */
@keyframes spin-tunnel {
  0% {
    transform: rotate(0deg) scale(1);
  }
  50% {
    transform: rotate(180deg) scale(1.2);
  }
  100% {
    transform: rotate(360deg) scale(1);
  }
}

@keyframes luminance-pulse {
  0%,
  100% {
    opacity: 0.1;
  }
  50% {
    opacity: 0.85;
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
