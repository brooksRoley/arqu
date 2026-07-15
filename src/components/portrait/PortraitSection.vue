<script setup lang="ts">
import { connectorConfigs } from '@/config/connectorConfig'

defineProps<{
  title: string
  body: string
  providers: string[]
}>()

function chipLabel(key: string): string {
  return connectorConfigs[key]?.label ?? key
}

function chipColor(key: string): string {
  return connectorConfigs[key]?.color ?? '#94a3b8'
}

function chipRoute(key: string): string {
  // Providers without a connector config page (e.g. steam) fall back to the hub
  return connectorConfigs[key] ? `/calibrate/${key}` : '/calibrate'
}
</script>

<template>
  <section class="space-y-4">
    <h3 class="text-lg sm:text-xl font-bold text-gray-200 tracking-tight">{{ title }}</h3>
    <p class="text-gray-400 font-mono text-sm sm:text-base leading-relaxed whitespace-pre-line">{{ body }}</p>
    <div v-if="providers.length" class="flex flex-wrap items-center gap-2 pt-1">
      <span class="text-[0.65rem] uppercase tracking-widest text-gray-600 font-mono">drawn from</span>
      <RouterLink
        v-for="p in providers"
        :key="p"
        :to="chipRoute(p)"
        class="text-xs font-mono px-3 py-1 rounded-full border transition-colors hover:bg-white/5"
        :style="{ borderColor: chipColor(p) + '50', color: chipColor(p) }"
      >{{ chipLabel(p) }}</RouterLink>
    </div>
  </section>
</template>
