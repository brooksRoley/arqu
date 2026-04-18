<script setup lang="ts">
const BARS = 40
</script>

<template>
  <figure class="enf">
    <div class="stage" aria-hidden="true">
      <div class="glow"></div>
      <div class="filter">
        <span
          v-for="i in BARS"
          :key="i"
          class="bar"
          :style="{ animationDelay: `${(i / BARS) * 6}s` }"
        ></span>
      </div>
      <div class="thoughts">
        <span class="thought t1"></span>
        <span class="thought t2"></span>
        <span class="thought t3"></span>
        <span class="thought t4"></span>
        <span class="thought t5"></span>
      </div>
    </div>
    <figcaption class="caption">
      <span class="legend"><span class="swatch swatch--filter"></span>the critical filter</span>
      <span class="legend"><span class="swatch swatch--thought"></span>incoming suggestion</span>
    </figcaption>
  </figure>
</template>

<style scoped>
.enf {
  margin: 0 0 2.5rem;
}

.stage {
  position: relative;
  height: 180px;
  background: radial-gradient(ellipse at center 65%, rgba(99, 102, 241, 0.08), transparent 70%);
  border: 1px solid #2a2a2a;
  border-radius: 10px;
  overflow: hidden;
}

.glow {
  position: absolute;
  inset: auto 0 0 0;
  height: 60%;
  background: radial-gradient(ellipse at center bottom, rgba(165, 180, 252, 0.18), transparent 75%);
  opacity: 0.6;
}

.filter {
  position: absolute;
  inset: 25% 8% auto 8%;
  display: flex;
  justify-content: space-between;
  height: 50%;
  pointer-events: none;
}

.bar {
  display: block;
  width: 1.5px;
  height: 100%;
  background: linear-gradient(to bottom, transparent 0%, #a5b4fc 30%, #a5b4fc 70%, transparent 100%);
  opacity: 0.85;
  animation: soften 6s ease-in-out infinite;
}

@keyframes soften {
  0%, 100% { opacity: 0.85; transform: scaleY(1); }
  50% { opacity: 0.15; transform: scaleY(0.55); }
}

.thoughts {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.thought {
  position: absolute;
  top: -10px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: radial-gradient(circle, #e2e8f0, rgba(226, 232, 240, 0));
  animation: fall 6s linear infinite;
}

.t1 { left: 18%; animation-delay: 0s; }
.t2 { left: 38%; animation-delay: 1.2s; }
.t3 { left: 52%; animation-delay: 2.4s; }
.t4 { left: 71%; animation-delay: 3.6s; }
.t5 { left: 86%; animation-delay: 4.8s; }

@keyframes fall {
  0% { top: -10px; opacity: 0; }
  10% { opacity: 1; }
  /* bounce off filter when filter is opaque */
  35% { top: 35%; opacity: 1; }
  45% { top: 28%; opacity: 0.7; }
  /* pass through during the soften window */
  55% { top: 55%; opacity: 1; }
  90% { top: 100%; opacity: 0.6; }
  100% { top: 110%; opacity: 0; }
}

.caption {
  display: flex;
  flex-wrap: wrap;
  gap: 1.25rem;
  margin-top: 0.75rem;
  font-size: 0.78rem;
  color: #64748b;
}

.legend {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
}

.swatch {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
}

.swatch--filter {
  background: #a5b4fc;
}

.swatch--thought {
  background: #e2e8f0;
}

@media (prefers-reduced-motion: reduce) {
  .bar, .thought {
    animation: none;
  }
  .bar {
    opacity: 0.5;
  }
}
</style>
