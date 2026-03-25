import { defineStore } from 'pinia'

export const useSyncStore = defineStore('sync', {
  state: () => ({
    isPlaying: false,
    currentTime: 0,
    duration: 0,
    volume: 0.8,
    masterBpm: 30 // 0.5Hz = 30 Beats Per Minute
  }),
  actions: {
    togglePlay() {
      this.isPlaying = !this.isPlaying
    },
    setTime(time) {
      this.currentTime = time
    }
  }
})
