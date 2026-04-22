<script setup lang="ts">
import { useMeditation } from '@/composables/useMeditation'

defineProps<{ show: boolean }>()
const emit = defineEmits<{ (e: 'close'): void }>()

const med = useMeditation()

function close() {
  med.stop()
  emit('close')
}
</script>

<template>
  <Teleport to="body">
    <Transition name="med-fade">
      <div v-if="show" class="meditation-overlay">
        <button class="med-close" @click="close">&times;</button>

        <!-- Pre-start screen -->
        <div v-if="!med.isActive.value" class="med-center">
          <div class="med-intro">
            <span class="med-intro-icon">&#x1F9D8;</span>
            <h2 class="med-intro-title">5-Minute Meditation</h2>
            <p class="med-intro-desc">
              Gentle music, nature sounds, and guided affirmations<br />
              to help you settle into the present moment.
            </p>
            <button class="med-begin-btn" @click="med.start()">Begin</button>
          </div>
        </div>

        <!-- Active meditation -->
        <div v-else class="med-center">
          <Transition name="affirmation" mode="out-in">
            <p :key="med.affirmationKey.value" class="med-affirmation">
              {{ med.currentAffirmation.value }}
            </p>
          </Transition>

          <div class="med-ring-wrap">
            <svg class="med-ring" viewBox="0 0 120 120">
              <circle class="ring-track" cx="60" cy="60" r="52" />
              <circle
                class="ring-progress"
                cx="60"
                cy="60"
                r="52"
                :stroke-dasharray="med.ringCircumference"
                :stroke-dashoffset="med.ringOffset.value"
              />
            </svg>
            <span class="med-time">{{ med.formatTime(med.remaining.value) }}</span>
          </div>

          <p v-if="med.isComplete.value" class="med-complete">Session complete</p>
        </div>

        <!-- Controls -->
        <div v-if="med.isActive.value && !med.isComplete.value" class="med-controls">
          <button class="med-pause-btn" @click="med.togglePause()">
            {{ med.isPaused.value ? '&#9654;' : '&#9208;' }}
          </button>

          <div class="volume-group">
            <label class="volume-label">Music</label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              class="volume-slider"
              :value="med.musicVolume.value"
              @input="med.setMusicVol(+($event.target! as any).value)"
            />
          </div>

          <div class="volume-group">
            <label class="volume-label">Nature</label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              class="volume-slider"
              :value="med.natureVolume.value"
              @input="med.setNatureVol(+($event.target! as any).value)"
            />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.meditation-overlay {
  position: fixed;
  inset: 0;
  z-index: 2000;
  background: rgba(5, 5, 15, 0.97);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.med-fade-enter-active,
.med-fade-leave-active { transition: opacity 0.5s ease; }
.med-fade-enter-from,
.med-fade-leave-to { opacity: 0; }

.med-close {
  position: absolute;
  top: 1rem;
  right: 1.25rem;
  background: none;
  border: none;
  color: #475569;
  font-size: 1.8rem;
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  line-height: 1;
  transition: color 0.15s;
  z-index: 1;
}
.med-close:hover { color: #94a3b8; }

.med-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2rem;
  padding: 0 2rem;
  max-width: 500px;
  text-align: center;
  flex: 1;
  justify-content: center;
}

.med-intro {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.med-intro-icon { font-size: 3rem; }

.med-intro-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #e2e8f0;
  margin: 0;
}

.med-intro-desc {
  font-size: 0.9rem;
  color: #94a3b8;
  line-height: 1.65;
  margin: 0;
}

.med-begin-btn {
  padding: 0.85rem 2.5rem;
  background: linear-gradient(135deg, rgba(217, 119, 6, 0.2), rgba(167, 139, 250, 0.15));
  border: 1px solid rgba(217, 119, 6, 0.35);
  border-radius: 0.6rem;
  color: #fbbf24;
  font-size: 1rem;
  font-weight: 600;
  font-family: inherit;
  letter-spacing: 0.04em;
  cursor: pointer;
  transition: background 0.2s, border-color 0.2s, box-shadow 0.2s;
  margin-top: 0.5rem;
}
.med-begin-btn:hover {
  background: linear-gradient(135deg, rgba(217, 119, 6, 0.35), rgba(167, 139, 250, 0.25));
  border-color: rgba(251, 191, 36, 0.5);
  box-shadow: 0 0 28px rgba(217, 119, 6, 0.15);
}

.med-affirmation {
  font-size: 1.25rem;
  color: #e2e8f0;
  line-height: 1.7;
  max-width: 420px;
  min-height: 3.5rem;
  margin: 0;
}

.affirmation-enter-active,
.affirmation-leave-active { transition: opacity 1.2s ease; }
.affirmation-enter-from,
.affirmation-leave-to { opacity: 0; }

.med-ring-wrap {
  position: relative;
  width: 120px;
  height: 120px;
}

.med-ring {
  width: 120px;
  height: 120px;
  transform: rotate(-90deg);
}

.ring-track {
  fill: none;
  stroke: rgba(255, 255, 255, 0.06);
  stroke-width: 3;
}

.ring-progress {
  fill: none;
  stroke: rgba(167, 139, 250, 0.5);
  stroke-width: 3;
  stroke-linecap: round;
  transition: stroke-dashoffset 0.5s ease;
}

.med-time {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
  color: #94a3b8;
  font-variant-numeric: tabular-nums;
}

.med-complete {
  font-size: 0.9rem;
  color: #a78bfa;
  font-weight: 500;
}

.med-controls {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  padding: 1.5rem 2rem;
  flex-wrap: wrap;
  justify-content: center;
}

.med-pause-btn {
  width: 2.75rem;
  height: 2.75rem;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #e2e8f0;
  font-size: 1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s, border-color 0.15s;
  flex-shrink: 0;
}
.med-pause-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.25);
}

.volume-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.volume-label {
  font-size: 0.7rem;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  min-width: 3rem;
}

.volume-slider {
  -webkit-appearance: none;
  appearance: none;
  width: 80px;
  height: 3px;
  background: rgba(255, 255, 255, 0.12);
  border-radius: 2px;
  outline: none;
}

.volume-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #94a3b8;
  cursor: pointer;
  border: none;
  transition: background 0.15s;
}
.volume-slider::-webkit-slider-thumb:hover { background: #e2e8f0; }

.volume-slider::-moz-range-thumb {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #94a3b8;
  cursor: pointer;
  border: none;
}

@media (max-width: 480px) {
  .med-affirmation { font-size: 1.1rem; padding: 0 1rem; }
  .med-controls { gap: 1rem; padding: 1rem; }
  .volume-slider { width: 60px; }
}
</style>
