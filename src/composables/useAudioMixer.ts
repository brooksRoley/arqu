import { ref, computed } from 'vue'

export interface AudioTrack {
  id: string
  name: string
  file: string
  audio: HTMLAudioElement | null
  playing: boolean
  volume: number
  currentTime: number
  duration: number
}

// Module-level state so it persists across consumers
const tracks = ref<AudioTrack[]>([])
const loaded = ref(false)

// Known audio files in /public/audio/
const audioFiles = [
  { name: 'Floating', file: 'floating.mp3' },
  { name: 'Coding Night', file: 'coding-night.mp3' }
]

function initTracks() {
  if (loaded.value) return
  tracks.value = audioFiles.map((f) => ({
    id: f.file,
    name: f.name,
    file: f.file,
    audio: null,
    playing: false,
    volume: 0.5,
    currentTime: 0,
    duration: 0
  }))
  loaded.value = true
}

function getOrCreateAudio(track: AudioTrack): HTMLAudioElement {
  if (!track.audio) {
    const el = new Audio(`/audio/${track.file}`)
    el.volume = track.volume
    el.loop = true
    el.addEventListener('timeupdate', () => {
      track.currentTime = el.currentTime
      track.duration = el.duration || 0
    })
    el.addEventListener('loadedmetadata', () => {
      track.duration = el.duration
    })
    track.audio = el
  }
  return track.audio
}

function toggleTrack(id: string) {
  const track = tracks.value.find((t) => t.id === id)
  if (!track) return

  const audio = getOrCreateAudio(track)
  if (track.playing) {
    audio.pause()
    track.playing = false
  } else {
    audio.play()
    track.playing = true
  }
}

function setVolume(id: string, vol: number) {
  const track = tracks.value.find((t) => t.id === id)
  if (!track) return
  track.volume = vol
  if (track.audio) {
    track.audio.volume = vol
  }
}

function seek(id: string, time: number) {
  const track = tracks.value.find((t) => t.id === id)
  if (!track) return
  const audio = getOrCreateAudio(track)
  audio.currentTime = time
  track.currentTime = time
}

function stopAll() {
  for (const track of tracks.value) {
    if (track.audio) {
      track.audio.pause()
      track.audio.currentTime = 0
    }
    track.playing = false
    track.currentTime = 0
  }
}

const anyPlaying = computed(() => tracks.value.some((t) => t.playing))

export function useAudioMixer() {
  initTracks()
  return {
    tracks,
    anyPlaying,
    toggleTrack,
    setVolume,
    seek,
    stopAll
  }
}
