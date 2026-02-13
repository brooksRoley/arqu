<script setup lang="ts">
import { useAudioMixer } from '@/composables/useAudioMixer'

const { tracks, anyPlaying, toggleTrack, setVolume, seek, stopAll } = useAudioMixer()

function formatTime(seconds: number): string {
  if (!seconds || !isFinite(seconds)) return '0:00'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

function onSeek(id: string, event: Event) {
  seek(id, parseFloat((event.target as HTMLInputElement).value))
}

function onVolume(id: string, event: Event) {
  setVolume(id, parseFloat((event.target as HTMLInputElement).value))
}
</script>

<template>
  <div class="mixer">
    <h1 class="mixer-title">Audio Mixer</h1>
    <p class="mixer-subtitle">Select and mix background tracks</p>

    <button v-if="anyPlaying" class="stop-all" @click="stopAll">Stop All</button>

    <div class="track-list">
      <div v-for="track in tracks" :key="track.id" class="track-card">
        <div class="track-top">
          <button
            class="play-btn"
            :class="{ 'play-btn--active': track.playing }"
            @click="toggleTrack(track.id)"
          >
            {{ track.playing ? '⏸' : '▶' }}
          </button>
          <span class="track-name">{{ track.name }}</span>
          <span class="track-time">
            {{ formatTime(track.currentTime) }} / {{ formatTime(track.duration) }}
          </span>
        </div>

        <!-- Progress / seek bar -->
        <div class="tracker">
          <input
            type="range"
            class="tracker-bar"
            min="0"
            :max="track.duration || 0"
            step="0.1"
            :value="track.currentTime"
            @input="onSeek(track.id, $event)"
          />
          <div
            class="tracker-fill"
            :style="{ width: track.duration ? (track.currentTime / track.duration * 100) + '%' : '0%' }"
          ></div>
        </div>

        <!-- Volume -->
        <div class="volume-row">
          <span class="volume-icon">{{ track.volume === 0 ? '🔇' : track.volume < 0.5 ? '🔉' : '🔊' }}</span>
          <input
            type="range"
            class="volume-slider"
            min="0"
            max="1"
            step="0.01"
            :value="track.volume"
            @input="onVolume(track.id, $event)"
          />
          <span class="volume-pct">{{ Math.round(track.volume * 100) }}%</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.mixer {
  max-width: 640px;
  margin: 0 auto;
}

.mixer-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: #e2e8f0;
  margin: 0 0 0.25rem;
}

.mixer-subtitle {
  color: #94a3b8;
  font-size: 0.95rem;
  margin: 0 0 1.5rem;
}

.stop-all {
  background: #991b1b;
  color: #fecaca;
  border: none;
  padding: 0.5rem 1.25rem;
  border-radius: 0.5rem;
  cursor: pointer;
  font-family: inherit;
  font-size: 0.85rem;
  margin-bottom: 1.25rem;
  transition: background 0.2s;
}

.stop-all:hover {
  background: #b91c1c;
}

.track-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.track-card {
  background: rgba(30, 30, 50, 0.8);
  border: 1px solid rgba(100, 100, 255, 0.15);
  border-radius: 0.75rem;
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  transition: border-color 0.2s;
}

.track-card:hover {
  border-color: rgba(99, 102, 241, 0.4);
}

.track-top {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.play-btn {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 50%;
  border: 2px solid #6366f1;
  background: transparent;
  color: #e2e8f0;
  cursor: pointer;
  font-size: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  flex-shrink: 0;
}

.play-btn:hover {
  background: rgba(99, 102, 241, 0.2);
}

.play-btn--active {
  background: #6366f1;
  color: #fff;
}

.track-name {
  font-weight: 600;
  font-size: 1rem;
  color: #e2e8f0;
  flex: 1;
}

.track-time {
  font-size: 0.8rem;
  color: #64748b;
  font-variant-numeric: tabular-nums;
}

/* Tracker / seek bar */
.tracker {
  position: relative;
  height: 6px;
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.08);
  overflow: visible;
}

.tracker-fill {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  background: #6366f1;
  border-radius: 3px;
  pointer-events: none;
  transition: width 0.15s linear;
}

.tracker-bar {
  position: absolute;
  top: -4px;
  left: 0;
  width: 100%;
  height: 14px;
  margin: 0;
  -webkit-appearance: none;
  appearance: none;
  background: transparent;
  cursor: pointer;
  z-index: 1;
}

.tracker-bar::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #e2e8f0;
  border: 2px solid #6366f1;
  cursor: grab;
}

.tracker-bar::-moz-range-thumb {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #e2e8f0;
  border: 2px solid #6366f1;
  cursor: grab;
}

/* Volume row */
.volume-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.volume-icon {
  font-size: 1rem;
  min-width: 1.25rem;
  text-align: center;
}

.volume-slider {
  flex: 1;
  -webkit-appearance: none;
  appearance: none;
  height: 4px;
  border-radius: 2px;
  background: rgba(255, 255, 255, 0.12);
  outline: none;
}

.volume-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #e2e8f0;
  cursor: pointer;
}

.volume-slider::-moz-range-thumb {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #e2e8f0;
  border: none;
  cursor: pointer;
}

.volume-pct {
  font-size: 0.8rem;
  color: #64748b;
  min-width: 2.5rem;
  text-align: right;
  font-variant-numeric: tabular-nums;
}

@media (max-width: 480px) {
  .mixer {
    padding: 0 0.5rem;
  }

  .track-card {
    padding: 1rem;
  }
}
</style>
