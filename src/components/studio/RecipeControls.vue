<template>
  <div class="space-y-3">
    <p class="text-[10px] text-white/35 leading-snug uppercase tracking-[0.15em]">
      Starting points — apply one, then edit it in Text and Sound.
    </p>

    <div
      v-for="recipe in recipes"
      :key="recipe.id"
      class="rounded-lg border bg-white/[0.02] p-3 space-y-2 transition-colors"
      :class="activeRecipeId === recipe.id ? 'border-emerald-500/30' : 'border-white/[0.06]'"
    >
      <div class="flex items-start justify-between gap-2">
        <div class="min-w-0 space-y-1">
          <span class="block text-[12px] text-white/80 tracking-wide">{{ recipe.name }}</span>
          <p class="text-[10px] text-white/40 leading-relaxed">{{ recipe.blurb }}</p>
          <router-link
            v-if="recipe.learnSlug"
            :to="`/learn/${recipe.learnSlug}`"
            class="inline-block text-[10px] text-emerald-400/70 hover:text-emerald-400 tracking-wider transition-colors"
          >
            Deep dive &rarr;
          </router-link>
        </div>
        <button
          class="cz-chip shrink-0"
          :class="activeRecipeId === recipe.id ? 'cz-chip-on' : 'cz-chip-off'"
          @click="$emit('apply', recipe)"
        >
          {{ activeRecipeId === recipe.id ? 'Applied' : 'Apply' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { GLASS_RECIPES, type GlassRecipe } from '@/data/glassRecipes'

defineProps<{ activeRecipeId?: string }>()

defineEmits<{
  (e: 'apply', recipe: GlassRecipe): void
}>()

const recipes = GLASS_RECIPES
</script>

<style scoped>
.cz-chip {
  @apply px-2.5 py-1 rounded-full text-[10px] tracking-wider border transition-all;
}
.cz-chip-on {
  @apply bg-emerald-500/15 border-emerald-500/30 text-emerald-300/90;
}
.cz-chip-off {
  @apply bg-transparent border-white/[0.08] text-white/40 hover:text-white/70;
}
</style>
