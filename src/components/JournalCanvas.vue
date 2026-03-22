<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'

const props = defineProps<{
  width?: number
  height?: number
  accentColor?: string
}>()

const emit = defineEmits<{
  save: [dataUrl: string]
}>()

const canvasRef = ref<HTMLCanvasElement | null>(null)
let ctx: CanvasRenderingContext2D | null = null
let drawing = false
let lastX = 0
let lastY = 0

const brushSize = ref(2)
const brushColor = ref(props.accentColor || '#a78bfa')
const canvasWidth = props.width || 600
const canvasHeight = props.height || 300

watch(() => props.accentColor, (c) => {
  if (c) brushColor.value = c
})

function getPos(e: MouseEvent | TouchEvent): { x: number; y: number } {
  const canvas = canvasRef.value!
  const rect = canvas.getBoundingClientRect()
  const scaleX = canvas.width / rect.width
  const scaleY = canvas.height / rect.height

  if ('touches' in e) {
    const touch = e.touches[0]
    return {
      x: (touch.clientX - rect.left) * scaleX,
      y: (touch.clientY - rect.top) * scaleY,
    }
  }
  return {
    x: (e.clientX - rect.left) * scaleX,
    y: (e.clientY - rect.top) * scaleY,
  }
}

function startDraw(e: MouseEvent | TouchEvent) {
  e.preventDefault()
  drawing = true
  const pos = getPos(e)
  lastX = pos.x
  lastY = pos.y
}

function draw(e: MouseEvent | TouchEvent) {
  if (!drawing || !ctx) return
  e.preventDefault()
  const pos = getPos(e)

  ctx.beginPath()
  ctx.moveTo(lastX, lastY)
  ctx.lineTo(pos.x, pos.y)
  ctx.strokeStyle = brushColor.value
  ctx.lineWidth = brushSize.value
  ctx.lineCap = 'round'
  ctx.lineJoin = 'round'
  ctx.stroke()

  lastX = pos.x
  lastY = pos.y
}

function endDraw() {
  drawing = false
}

function clear() {
  if (!ctx) return
  ctx.clearRect(0, 0, canvasWidth, canvasHeight)
}

function save() {
  if (!canvasRef.value) return
  const dataUrl = canvasRef.value.toDataURL('image/png')
  emit('save', dataUrl)
}

onMounted(() => {
  if (canvasRef.value) {
    ctx = canvasRef.value.getContext('2d')
  }
})

onUnmounted(() => {
  ctx = null
})
</script>

<template>
  <div class="journal-canvas">
    <div class="canvas-toolbar">
      <label class="toolbar-item">
        <span class="toolbar-label">Size</span>
        <input type="range" min="1" max="12" v-model.number="brushSize" class="range-input" />
      </label>
      <label class="toolbar-item">
        <span class="toolbar-label">Color</span>
        <input type="color" v-model="brushColor" class="color-input" />
      </label>
      <button class="toolbar-btn" @click="clear">Clear</button>
      <button class="toolbar-btn toolbar-btn--save" @click="save">Save Drawing</button>
    </div>

    <canvas
      ref="canvasRef"
      :width="canvasWidth"
      :height="canvasHeight"
      class="draw-surface"
      @mousedown="startDraw"
      @mousemove="draw"
      @mouseup="endDraw"
      @mouseleave="endDraw"
      @touchstart="startDraw"
      @touchmove="draw"
      @touchend="endDraw"
    />
  </div>
</template>

<style scoped>
.journal-canvas {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.canvas-toolbar {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.toolbar-item {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.toolbar-label {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #64748b;
}

.range-input {
  width: 60px;
  accent-color: #6366f1;
}

.color-input {
  width: 24px;
  height: 24px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  background: none;
  cursor: pointer;
  padding: 0;
}

.toolbar-btn {
  font-size: 0.75rem;
  padding: 0.3rem 0.65rem;
  border-radius: 0.35rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.04);
  color: #94a3b8;
  cursor: pointer;
  font-family: inherit;
  transition: background 0.15s, color 0.15s;
}

.toolbar-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #e2e8f0;
}

.toolbar-btn--save {
  border-color: rgba(99, 102, 241, 0.3);
  color: #a5b4fc;
}

.toolbar-btn--save:hover {
  background: rgba(99, 102, 241, 0.15);
}

.draw-surface {
  width: 100%;
  max-width: 600px;
  height: auto;
  aspect-ratio: 2 / 1;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 0.5rem;
  background: rgba(0, 0, 0, 0.3);
  cursor: crosshair;
  touch-action: none;
}
</style>
