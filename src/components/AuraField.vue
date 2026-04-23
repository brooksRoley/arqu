<script setup lang="ts">
import { computed } from 'vue'

interface FittingData {
  body_type: 'female' | 'male'
  height: number
  build: number
  [key: string]: unknown
}

const props = defineProps<{
  fitting: FittingData | null
  hasSpotify: boolean
  hasOracle: boolean
  hasPsychometric: boolean
  hasActivity: boolean
  hasAttachment: boolean
}>()

const heightScale = computed(() => {
  const h = props.fitting?.height ?? 68
  return 0.82 + (h - 56) / 26 * 0.36
})
const buildScale = computed(() => {
  const b = props.fitting?.build ?? 5
  return 0.78 + (b - 1) / 9 * 0.56
})
const isMale = computed(() => props.fitting?.body_type === 'male')

const silhouetteHeight = computed(() => Math.round(400 * heightScale.value))
const silhouetteWidth = computed(() => Math.round(120 * buildScale.value * (isMale.value ? 1.1 : 1)))

const layers = computed(() => {
  const result: { color: string; opacity: number; offset: number }[] = []
  if (props.hasPsychometric)
    result.push({ color: '#8B5CF6', opacity: 0.35, offset: 10 })
  if (props.hasOracle)
    result.push({ color: '#EC4899', opacity: 0.25, offset: 25 })
  if (props.hasSpotify)
    result.push({ color: '#22C55E', opacity: 0.18, offset: 40 })
  if (props.hasAttachment)
    result.push({ color: '#F59E0B', opacity: 0.14, offset: 55 })
  if (props.hasActivity)
    result.push({ color: '#3B82F6', opacity: 0.10, offset: 70 })
  return result
})
</script>

<template>
  <div class="relative flex items-center justify-center" :style="{ minHeight: `${silhouetteHeight + 160}px` }">
    <div
      v-for="(layer, i) in layers"
      :key="i"
      class="absolute rounded-[50%] transition-all duration-700"
      :style="{
        width: `${silhouetteWidth + layer.offset * 2}px`,
        height: `${silhouetteHeight + layer.offset * 2}px`,
        background: `radial-gradient(ellipse at center, ${layer.color}${Math.round(layer.opacity * 255).toString(16).padStart(2, '0')} 0%, transparent 70%)`,
        filter: `blur(${8 + i * 4}px)`,
      }"
    />
    <div
      class="relative rounded-[40%_40%_35%_35%/25%_25%_40%_40%] border border-white/10"
      :style="{
        width: `${silhouetteWidth}px`,
        height: `${silhouetteHeight}px`,
        background: 'rgba(255,255,255,0.04)',
      }"
    />
  </div>
</template>
