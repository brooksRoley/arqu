import { ref, readonly } from 'vue'
import * as Tone from 'tone'

/**
 * Records the Glass Studio composition to a downloadable video file.
 *
 * Pipeline:
 *   1. Composites each video frame + text overlay onto a hidden canvas.
 *   2. canvas.captureStream(30) → video track.
 *   3. MediaStreamAudioDestinationNode captures both the original media
 *      audio and the Tone.js synthesis master into one audio track.
 *   4. MediaRecorder merges the two tracks and writes chunks.
 *   5. On media end → stop → Blob → download link.
 *
 * The export runs in real-time (duration = media duration).
 */

const isRecording = ref(false)
const progress = ref(0)

let recorder: MediaRecorder | null = null
let chunks: Blob[] = []
let exportCanvas: HTMLCanvasElement | null = null
let exportCtx: CanvasRenderingContext2D | null = null
let rafId: number | undefined
let endHandler: (() => void) | null = null

/** Pick the best supported container. */
function pickMime(): string {
  for (const mime of [
    'video/mp4;codecs=avc1,mp4a.40.2',
    'video/webm;codecs=vp9,opus',
    'video/webm;codecs=vp8,opus',
    'video/webm',
  ]) {
    if (MediaRecorder.isTypeSupported(mime)) return mime
  }
  return 'video/webm'
}

export function useGlassExport() {
  async function startExport(
    mediaEl: HTMLVideoElement,
    text: string,
    analyserNode: AnalyserNode | null,
    toneMasterNode: GainNode,
  ) {
    if (isRecording.value) return
    await Tone.start()

    const ctx = Tone.getContext().rawContext as AudioContext

    // ── Canvas for compositing ──
    const w = mediaEl.videoWidth || 1920
    const h = mediaEl.videoHeight || 1080
    exportCanvas = document.createElement('canvas')
    exportCanvas.width = w
    exportCanvas.height = h
    exportCtx = exportCanvas.getContext('2d')!

    // ── Capture streams ──
    const canvasStream = exportCanvas.captureStream(30)
    const audioDest = ctx.createMediaStreamDestination()

    // Route original audio + tone synthesis into the export bus
    if (analyserNode) analyserNode.connect(audioDest)
    toneMasterNode.connect(audioDest)

    const combined = new MediaStream([
      ...canvasStream.getVideoTracks(),
      ...audioDest.stream.getAudioTracks(),
    ])

    // ── MediaRecorder ──
    const mimeType = pickMime()
    chunks = []
    recorder = new MediaRecorder(combined, { mimeType, videoBitsPerSecond: 5_000_000 })

    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunks.push(e.data)
    }

    recorder.onstop = () => {
      // Download the file
      const ext = mimeType.startsWith('video/mp4') ? 'mp4' : 'webm'
      const blob = new Blob(chunks, { type: mimeType })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `glass-export-${Date.now()}.${ext}`
      a.click()
      setTimeout(() => URL.revokeObjectURL(url), 5000)

      // Tear down export-only connections
      if (analyserNode) try { analyserNode.disconnect(audioDest) } catch { /* ok */ }
      try { toneMasterNode.disconnect(audioDest) } catch { /* ok */ }

      isRecording.value = false
      progress.value = 0
    }

    // ── Render loop ──
    function renderFrame() {
      if (!isRecording.value || !exportCtx || !exportCanvas) return
      const cw = exportCanvas.width
      const ch = exportCanvas.height

      // Video frame (or dark fill for audio-only)
      if (mediaEl.videoWidth > 0) {
        exportCtx.drawImage(mediaEl, 0, 0, cw, ch)
      } else {
        exportCtx.fillStyle = '#0a0a0a'
        exportCtx.fillRect(0, 0, cw, ch)
      }

      // Text overlay (difference composite ≈ mix-blend-exclusion)
      if (text) {
        exportCtx.save()
        exportCtx.globalCompositeOperation = 'difference'
        const fontSize = Math.min(cw * 0.1, 140)
        exportCtx.font = `900 ${fontSize}px system-ui, -apple-system, sans-serif`
        exportCtx.fillStyle = 'white'
        exportCtx.textAlign = 'center'
        exportCtx.textBaseline = 'middle'

        // Simple word-wrap
        const words = text.split(/\s+/)
        const maxW = cw * 0.85
        const lines: string[] = []
        let cur = ''
        for (const w of words) {
          const test = cur ? `${cur} ${w}` : w
          if (exportCtx.measureText(test).width > maxW && cur) {
            lines.push(cur)
            cur = w
          } else {
            cur = test
          }
        }
        if (cur) lines.push(cur)

        const lh = fontSize * 1.1
        const startY = ch / 2 - ((lines.length - 1) * lh) / 2
        lines.forEach((line, i) => {
          exportCtx!.fillText(line, cw / 2, startY + i * lh)
        })
        exportCtx.restore()
      }

      // Progress
      if (mediaEl.duration && isFinite(mediaEl.duration)) {
        progress.value = mediaEl.currentTime / mediaEl.duration
      }

      rafId = requestAnimationFrame(renderFrame)
    }

    // ── Kick off ──
    mediaEl.currentTime = 0
    recorder.start(200) // collect chunks every 200ms
    isRecording.value = true

    // Wait for seek, then play
    mediaEl.onseeked = () => {
      mediaEl.onseeked = null
      mediaEl.play()
    }

    rafId = requestAnimationFrame(renderFrame)

    // Stop on media end
    endHandler = () => stopExport()
    mediaEl.addEventListener('ended', endHandler, { once: true })
  }

  function stopExport() {
    if (rafId) cancelAnimationFrame(rafId)
    if (recorder && recorder.state !== 'inactive') recorder.stop()
    // endHandler is cleaned up by { once: true }
    endHandler = null
  }

  return {
    isRecording: readonly(isRecording),
    progress: readonly(progress),
    startExport,
    stopExport,
  }
}
