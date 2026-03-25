import { ref, watch } from 'vue'
import { useSyncStore } from '@/stores/useSyncStore'

export function useAudioEngine(audioFileUrl) {
  const store = useSyncStore()
  let audioContext = null
  let audioElement = null
  let track = null
  let gainNode = null
  let animationFrameId = null

  const initAudio = () => {
    if (audioContext) return

    audioContext = new (window.AudioContext || window.webkitAudioContext)()
    audioElement = new Audio(audioFileUrl)

    // Route the audio element through the Web Audio API
    track = audioContext.createMediaElementSource(audioElement)
    gainNode = audioContext.createGain()

    track.connect(gainNode).connect(audioContext.destination)

    audioElement.addEventListener('loadedmetadata', () => {
      store.duration = audioElement.duration
    })

    // The Master Clock Loop
    const updateTime = () => {
      if (store.isPlaying) {
        store.setTime(audioElement.currentTime)
        animationFrameId = requestAnimationFrame(updateTime)
      }
    }

    // Watch the Pinia store for Play/Pause commands
    watch(
      () => store.isPlaying,
      (playing) => {
        if (audioContext.state === 'suspended') audioContext.resume()

        if (playing) {
          audioElement.play()
          updateTime()
        } else {
          audioElement.pause()
          cancelAnimationFrame(animationFrameId)
        }
      },
      { immediate: true }
    )

    // Watch the Pinia store for Volume changes
    watch(
      () => store.volume,
      (newVol) => {
        if (gainNode) gainNode.gain.value = newVol
      },
      { immediate: true }
    )
  }

  return { initAudio }
}
