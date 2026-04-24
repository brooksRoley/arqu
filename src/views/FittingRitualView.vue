<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useRevealStore } from '@/composables/useRevealStore'
import type { FittingData } from '@/composables/useVibeStore'

const router = useRouter()
const route = useRoute()
const matchId = route.params.matchId as string
const { fetchReveal, saveFitting, revealData } = useRevealStore()

const phase = ref<'loading' | 'self' | 'ideal' | 'done'>('loading')
const saving = ref(false)

// ── Configurator state (mirrors Fitting.vue) ─────────────────────
type BodyType = 'female' | 'male'
const bodyType = ref<BodyType>('female')
const body = reactive({
  height: 68, build: 5, chest: 40, waist: 34, hips: 40, shoulders: 18,
})
const skinColor = ref('#C68642')
const skinShadow = ref('#A0522D')
const hairColor = ref('#3B1F0A')
const hairLength = ref<'short' | 'medium' | 'long'>('medium')
const suitColor = ref('#2E86AB')
const suitColorDark = ref('#1A5276')

// Suit-specific
const femaleSuit = reactive({
  topStyle: 'underwire' as string,
  rise: 'mid' as string,
  coverage: 'full' as string,
})
const maleSuit = reactive({
  top: 'none' as string,
  bottom: 'board-knee' as string,
  wetsuit: 'none' as string,
})

const skinTones = [
  { color: '#FDDBB4', shadow: '#E8B88A' },
  { color: '#EDB98A', shadow: '#C88B5A' },
  { color: '#C68642', shadow: '#A0522D' },
  { color: '#8D5524', shadow: '#6B3A0F' },
  { color: '#4A2912', shadow: '#2E1508' },
  { color: '#FEE0C0', shadow: '#ECBF98' },
]
const hairColors = ['#3B1F0A', '#6B3A0F', '#C49A3C', '#E8D5A3', '#1A1A1A', '#8B0000', '#6B478B', '#4A90D9']
const suitOptions = [
  { color: '#2E86AB', dark: '#1A5276' },
  { color: '#C0458A', dark: '#8B1A5E' },
  { color: '#E8453C', dark: '#B03030' },
  { color: '#27AE60', dark: '#1A7A42' },
  { color: '#F39C12', dark: '#B07A0A' },
  { color: '#1A1A2E', dark: '#0D0D1A' },
  { color: '#FFFFFF', dark: '#C8C8C8' },
  { color: '#E8C3E8', dark: '#C090C0' },
]

function resetToDefaults() {
  bodyType.value = 'female'
  body.height = 68; body.build = 5; body.chest = 40
  body.waist = 34; body.hips = 40; body.shoulders = 18
  skinColor.value = '#C68642'; skinShadow.value = '#A0522D'
  hairColor.value = '#3B1F0A'; hairLength.value = 'medium'
  suitColor.value = '#2E86AB'; suitColorDark.value = '#1A5276'
  femaleSuit.topStyle = 'underwire'; femaleSuit.rise = 'mid'; femaleSuit.coverage = 'full'
  maleSuit.top = 'none'; maleSuit.bottom = 'board-knee'; maleSuit.wetsuit = 'none'
}

function collectFittingData(): FittingData {
  return {
    body_type: bodyType.value,
    height: body.height,
    build: body.build,
    chest: body.chest,
    waist: body.waist,
    hips: body.hips,
    shoulders: body.shoulders,
    skin_color: skinColor.value,
    skin_shadow: skinShadow.value,
    hair_color: hairColor.value,
    hair_length: hairLength.value,
    suit_color: suitColor.value,
    suit_color_dark: suitColorDark.value,
    ...(bodyType.value === 'female'
      ? { top_style: femaleSuit.topStyle, rise: femaleSuit.rise, coverage: femaleSuit.coverage }
      : { top: maleSuit.top, bottom: maleSuit.bottom, wetsuit: maleSuit.wetsuit }
    ),
  }
}

async function submitPhase() {
  saving.value = true
  try {
    const currentPhase = phase.value as 'self' | 'ideal'
    await saveFitting(currentPhase, collectFittingData())
    if (currentPhase === 'self') {
      resetToDefaults()
      phase.value = 'ideal'
    } else {
      router.push(`/reveal/${matchId}`)
    }
  } finally {
    saving.value = false
  }
}

function setBodyType(type: BodyType) {
  bodyType.value = type
  if (type === 'male') {
    body.chest = 42; body.waist = 36; body.hips = 38; body.shoulders = 20
  } else {
    body.chest = 38; body.waist = 32; body.hips = 42; body.shoulders = 16
  }
}

onMounted(async () => {
  await fetchReveal(matchId)
  const hasSelf = revealData.value?.self?.fitting_self != null
  const hasIdeal = revealData.value?.self?.fitting_ideal != null
  if (hasSelf && hasIdeal) {
    router.replace(`/reveal/${matchId}`)
  } else if (hasSelf) {
    phase.value = 'ideal'
  } else {
    phase.value = 'self'
  }
})
</script>

<template>
  <div class="min-h-screen bg-gray-950 text-gray-100">
    <!-- Loading -->
    <div v-if="phase === 'loading'" class="flex items-center justify-center h-screen">
      <div class="text-gray-500">Loading...</div>
    </div>

    <!-- Ritual phases -->
    <div v-else class="flex flex-col lg:flex-row h-screen">
      <!-- Header / prompt -->
      <div class="lg:hidden px-6 pt-6 pb-2">
        <h1 class="text-lg font-semibold">
          {{ phase === 'self' ? 'Show us you' : 'Show us what you see' }}
        </h1>
        <p class="text-sm text-gray-500 mt-1">
          {{ phase === 'self'
            ? 'Build your avatar — this is how you see yourself.'
            : 'Now build the person you imagine. Before we show you your match.' }}
        </p>
      </div>

      <!-- SVG figure panel -->
      <div class="flex-shrink-0 lg:w-[380px] flex items-start justify-center p-6 bg-gray-900/50 overflow-y-auto">
        <div class="text-center">
          <div class="hidden lg:block mb-8">
            <h1 class="text-lg font-semibold">
              {{ phase === 'self' ? 'Show us you' : 'Show us what you see' }}
            </h1>
            <p class="text-sm text-gray-500 mt-1 max-w-[280px] mx-auto">
              {{ phase === 'self'
                ? 'Build your avatar — this is how you see yourself.'
                : 'Now build the person you imagine. Before we show you your match.' }}
            </p>
          </div>
          <div class="text-gray-600 text-sm">[Avatar preview]</div>
        </div>
      </div>

      <!-- Controls -->
      <div class="flex-1 overflow-y-auto p-6 space-y-6">
        <!-- Body type toggle -->
        <section class="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 class="text-xs uppercase tracking-widest text-gray-500 mb-3">Body Type</h3>
          <div class="flex rounded-lg overflow-hidden border border-gray-700">
            <button
              class="flex-1 py-2 text-sm transition-colors"
              :class="bodyType === 'female' ? 'bg-purple-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'"
              @click="setBodyType('female')"
            >Female</button>
            <button
              class="flex-1 py-2 text-sm transition-colors"
              :class="bodyType === 'male' ? 'bg-purple-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'"
              @click="setBodyType('male')"
            >Male</button>
          </div>
        </section>

        <!-- Measurements -->
        <section class="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-3">
          <h3 class="text-xs uppercase tracking-widest text-gray-500 mb-1">Body</h3>
          <div v-for="[key, label, min, max] in ([
            ['height', 'Height', 56, 82],
            ['build', 'Build', 1, 10],
            ['shoulders', 'Shoulders', 14, 24],
            ['chest', bodyType === 'male' ? 'Chest' : 'Bust', 26, 58],
            ['waist', 'Waist', 22, 58],
            ['hips', 'Hips', 28, 64],
          ] as const)" :key="key">
            <div class="flex justify-between text-sm text-gray-400">
              <span>{{ label }}</span>
              <span class="text-amber-300 tabular-nums">{{ (body as any)[key] }}</span>
            </div>
            <input type="range" v-model.number="(body as any)[key]" :min="min" :max="max" class="w-full accent-purple-500" />
          </div>
        </section>

        <!-- Appearance -->
        <section class="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-3">
          <h3 class="text-xs uppercase tracking-widest text-gray-500 mb-1">Appearance</h3>
          <div>
            <div class="text-sm text-gray-400 mb-2">Skin Tone</div>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="tone in skinTones" :key="tone.color"
                class="w-7 h-7 rounded-full border-2 transition-transform"
                :class="skinColor === tone.color ? 'border-white scale-110' : 'border-transparent'"
                :style="{ background: tone.color }"
                @click="skinColor = tone.color; skinShadow = tone.shadow"
              />
            </div>
          </div>
          <div>
            <div class="text-sm text-gray-400 mb-2">Hair Color</div>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="h in hairColors" :key="h"
                class="w-7 h-7 rounded-full border-2 transition-transform"
                :class="hairColor === h ? 'border-white scale-110' : 'border-transparent'"
                :style="{ background: h }"
                @click="hairColor = h"
              />
            </div>
          </div>
          <div>
            <div class="text-sm text-gray-400 mb-2">Hair Length</div>
            <div class="flex gap-2">
              <button
                v-for="len in (['short', 'medium', 'long'] as const)" :key="len"
                class="px-3 py-1.5 rounded-lg text-xs border transition-colors"
                :class="hairLength === len ? 'bg-purple-600 border-purple-600 text-white' : 'bg-gray-800 border-gray-700 text-gray-400'"
                @click="hairLength = len"
              >{{ len }}</button>
            </div>
          </div>
        </section>

        <!-- Suit color -->
        <section class="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-3">
          <h3 class="text-xs uppercase tracking-widest text-gray-500 mb-1">Swimwear Color</h3>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="s in suitOptions" :key="s.color"
              class="w-7 h-7 rounded-full border-2 transition-transform"
              :class="suitColor === s.color ? 'border-white scale-110' : 'border-transparent'"
              :style="{ background: s.color }"
              @click="suitColor = s.color; suitColorDark = s.dark"
            />
          </div>
        </section>

        <!-- Submit -->
        <button
          @click="submitPhase"
          :disabled="saving"
          class="w-full py-3 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-medium transition-colors disabled:opacity-50"
        >
          {{ saving ? 'Saving...' : phase === 'self' ? 'Continue →' : 'Reveal my match →' }}
        </button>
      </div>
    </div>
  </div>
</template>
