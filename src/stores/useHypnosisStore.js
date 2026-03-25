import { defineStore } from 'pinia'

export const useHypnosisStore = defineStore('hypnosis', {
  state: () => ({
    isActive: false, // Toggles the full-screen overlay
    frequencyHz: 0.5, // The 0.5Hz beat (1 cycle per 2 seconds)
    isColorAltered: false // Toggles the perceptual color shift
  }),
  getters: {
    // Converts the Hz frequency into a CSS animation duration (e.g., 0.5Hz = "2s")
    pulseDuration: (state) => `${1 / state.frequencyHz}s`,
    // A slower rotation for the kinetic tunnel effect
    spinDuration: (state) => `${(1 / state.frequencyHz) * 10}s`
  },
  actions: {
    startSession() {
      this.isActive = true
    },
    stopSession() {
      this.isActive = false
      this.isColorAltered = false
    },
    triggerColorShift() {
      this.isColorAltered = !this.isColorAltered
    }
  }
})
