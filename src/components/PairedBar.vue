<script setup lang="ts">
defineProps<{
  label: string
  selfValue: number
  matchValue: number
  selfColor?: string
  matchColor?: string
}>()
</script>

<template>
  <div class="flex items-center gap-2">
    <span class="text-xs text-gray-500 w-28 truncate">{{ label }}</span>
    <div class="flex-1 h-2.5 bg-gray-800 rounded-full relative overflow-hidden">
      <div
        class="absolute inset-y-0 left-0 rounded-full opacity-70"
        :style="{
          width: `${Math.min(selfValue * 100, 100)}%`,
          background: selfColor || '#8B5CF6',
        }"
      />
      <div
        class="absolute inset-y-0 left-0 rounded-full opacity-50 border-r-2 border-white/30"
        :style="{
          width: `${Math.min(matchValue * 100, 100)}%`,
          background: matchColor || '#EC4899',
        }"
      />
    </div>
    <span class="text-xs text-gray-500 w-16 text-right tabular-nums">
      {{ selfValue.toFixed(2) }} / {{ matchValue.toFixed(2) }}
    </span>
  </div>
</template>
