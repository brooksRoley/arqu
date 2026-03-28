<template>
  <div class="min-h-screen bg-black text-lime-400 p-8 font-mono">
    <header class="mb-12 border-b border-lime-800 pb-4">
      <h1 class="text-3xl font-bold tracking-tighter uppercase">Your Psychology</h1>
      <p class="text-lime-600 mt-2">The architecture of your resonance.</p>
    </header>

    <!-- Assessment Intake Form (Mock) -->
    <div v-if="!profile && !loading" class="max-w-xl border border-lime-800 p-6 bg-black/50 mx-auto">
      <h2 class="text-xl mb-4 text-white uppercase tracking-widest text-center">Baseline Assessment Required</h2>
      <p class="mb-8 text-lime-600 text-sm italic text-center">To synchronize your compatibility vectors, complete the multi-phasic intake covering Big Five, Attachment, and Values.</p>
      
      <form @submit.prevent="submitAssessment" class="space-y-6">
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block mb-1 text-xs text-lime-600 uppercase">Openness (0-1)</label>
            <input type="number" v-model.number="form.O_score" min="0" max="1" step="0.1" class="w-full bg-black border border-lime-800 p-2 text-lime-300 focus:border-lime-400 outline-none" required />
          </div>
          <div>
            <label class="block mb-1 text-xs text-lime-600 uppercase">Conscientiousness (0-1)</label>
            <input type="number" v-model.number="form.C_score" min="0" max="1" step="0.1" class="w-full bg-black border border-lime-800 p-2 text-lime-300 focus:border-lime-400 outline-none" required />
          </div>
          <div>
            <label class="block mb-1 text-xs text-lime-600 uppercase">Extraversion (0-1)</label>
            <input type="number" v-model.number="form.E_score" min="0" max="1" step="0.1" class="w-full bg-black border border-lime-800 p-2 text-lime-300 focus:border-lime-400 outline-none" required />
          </div>
          <div>
            <label class="block mb-1 text-xs text-lime-600 uppercase">Agreeableness (0-1)</label>
            <input type="number" v-model.number="form.A_score" min="0" max="1" step="0.1" class="w-full bg-black border border-lime-800 p-2 text-lime-300 focus:border-lime-400 outline-none" required />
          </div>
          <div>
            <label class="block mb-1 text-xs text-lime-600 uppercase">Neuroticism (0-1)</label>
            <input type="number" v-model.number="form.N_score" min="0" max="1" step="0.1" class="w-full bg-black border border-lime-800 p-2 text-lime-300 focus:border-lime-400 outline-none" required />
          </div>
        </div>
        
        <div class="border-t border-lime-900 pt-6 grid grid-cols-2 gap-4">
          <div>
            <label class="block mb-1 text-xs text-lime-600 uppercase">Attachment Anxiety (0-1)</label>
            <input type="number" v-model.number="form.anxiety_score" min="0" max="1" step="0.1" class="w-full bg-black border border-lime-800 p-2 text-lime-300 focus:border-lime-400 outline-none" required />
          </div>
          <div>
            <label class="block mb-1 text-xs text-lime-600 uppercase">Attachment Avoidance (0-1)</label>
            <input type="number" v-model.number="form.avoidance_score" min="0" max="1" step="0.1" class="w-full bg-black border border-lime-800 p-2 text-lime-300 focus:border-lime-400 outline-none" required />
          </div>
        </div>

        <div class="border-t border-lime-900 pt-6">
          <label class="block mb-1 text-xs text-lime-600 uppercase">Primary Love Language</label>
          <select v-model="form.love_language" class="w-full bg-black border border-lime-800 p-2 text-lime-300 focus:border-lime-400 outline-none">
            <option>Words of Affirmation</option>
            <option>Quality Time</option>
            <option>Receiving Gifts</option>
            <option>Acts of Service</option>
            <option>Physical Touch</option>
          </select>
        </div>

        <button type="submit" class="w-full bg-lime-900/40 hover:bg-lime-800 text-lime-300 border border-lime-600 p-3 mt-4 transition-colors uppercase tracking-widest text-sm">
          Initialize Sync
        </button>
      </form>
    </div>

    <!-- Dashboard -->
    <div v-else-if="profile" class="grid grid-cols-1 lg:grid-cols-2 gap-8">
      
      <!-- Left Column -->
      <div class="space-y-8">
        <!-- Big Five Chart -->
        <section class="border border-lime-800 p-6 bg-black/30">
          <h2 class="text-xl mb-4 text-white uppercase tracking-widest text-center">OCEAN Signature</h2>
          <div class="flex justify-center items-center py-4">
            <!-- Simple SVG Radar stub (A real implementation would compute polygon points) -->
            <svg width="240" height="240" viewBox="0 0 200 200" class="overflow-visible">
              <!-- Grid -->
              <polygon points="100,20 176,75 147,164 53,164 24,75" fill="none" stroke="#1a2e1a" stroke-width="1"/>
              <polygon points="100,60 138,87 123,132 77,132 62,87" fill="none" stroke="#1a2e1a" stroke-width="1"/>
              <line x1="100" y1="100" x2="100" y2="20" stroke="#1a2e1a" />
              <line x1="100" y1="100" x2="176" y2="75" stroke="#1a2e1a" />
              <line x1="100" y1="100" x2="147" y2="164" stroke="#1a2e1a" />
              <line x1="100" y1="100" x2="53" y2="164" stroke="#1a2e1a" />
              <line x1="100" y1="100" x2="24" y2="75" stroke="#1a2e1a" />
              
              <!-- Data Polygon -->
              <polygon 
                :points="radarPoints" 
                fill="rgba(163, 230, 53, 0.25)" 
                stroke="#a3e635" 
                stroke-width="1.5"
              />
              
              <!-- Labels -->
              <text x="100" y="8" fill="#a3e635" font-size="8" text-anchor="middle" class="uppercase tracking-widest">Openness</text>
              <text x="185" y="75" fill="#a3e635" font-size="8" text-anchor="start" class="uppercase tracking-widest">Conscientiousness</text>
              <text x="150" y="175" fill="#a3e635" font-size="8" text-anchor="start" class="uppercase tracking-widest">Extraversion</text>
              <text x="50" y="175" fill="#a3e635" font-size="8" text-anchor="end" class="uppercase tracking-widest">Agreeableness</text>
              <text x="15" y="75" fill="#a3e635" font-size="8" text-anchor="end" class="uppercase tracking-widest">Neuroticism</text>
            </svg>
          </div>
          <div class="mt-4 grid grid-cols-2 gap-4 text-xs tracking-wider">
            <div class="flex justify-between border-b border-lime-900/50 py-1"><span>Openness:</span> <span class="text-white">{{profile.ipip_neo_scores.O}}</span></div>
            <div class="flex justify-between border-b border-lime-900/50 py-1"><span>Conscientiousness:</span> <span class="text-white">{{profile.ipip_neo_scores.C}}</span></div>
            <div class="flex justify-between border-b border-lime-900/50 py-1"><span>Extraversion:</span> <span class="text-white">{{profile.ipip_neo_scores.E}}</span></div>
            <div class="flex justify-between border-b border-lime-900/50 py-1"><span>Agreeableness:</span> <span class="text-white">{{profile.ipip_neo_scores.A}}</span></div>
            <div class="flex justify-between py-1"><span>Neuroticism:</span> <span class="text-white">{{profile.ipip_neo_scores.N}}</span></div>
          </div>
        </section>

        <!-- Explainer -->
        <section class="border border-lime-800 p-6 bg-black/30">
          <h2 class="text-xl mb-4 text-white uppercase tracking-widest">Matching Ontology</h2>
          <p class="text-xs text-lime-500 leading-relaxed mb-4">
            Your vectors dictate your resonance in the algorithm. We weight <strong>Attachment Compatibility</strong> highest (seeking secure dynamics), followed by <strong>Values Congruence</strong>.
          </p>
          <p class="text-xs text-lime-500 leading-relaxed">
             <strong>Big Five</strong> similarity stabilizes long-term satisfaction while extraversion complementarity provides friction. The agent incorporates your Spotify and behavioral signatures to fine-tune raw psychological scores.
          </p>
        </section>

      </div>

      <!-- Right Column -->
      <div class="space-y-8">
        
        <!-- Attachment Quadrant -->
        <section class="border border-lime-800 p-6 bg-black/30">
          <h2 class="text-xl mb-6 text-white uppercase tracking-widest text-center">Attachment Matrix</h2>
          <div class="relative w-full shadow-inner aspect-square max-w-[280px] mx-auto border border-lime-900 bg-lime-950/20">
            <!-- Axes -->
            <div class="absolute inset-y-0 left-1/2 w-px bg-lime-800"></div>
            <div class="absolute inset-x-0 top-1/2 h-px bg-lime-800"></div>
            <!-- Labels -->
            <span class="absolute top-2 left-1/2 -translate-x-1/2 text-[9px] uppercase tracking-widest text-lime-600 bg-black/80 px-1">High Anxiety</span>
            <span class="absolute bottom-2 left-1/2 -translate-x-1/2 text-[9px] uppercase tracking-widest text-lime-600 bg-black/80 px-1">Low Anxiety</span>
            <span class="absolute left-2 top-1/2 -translate-y-1/2 text-[9px] uppercase tracking-widest text-lime-600 -rotate-90 origin-left bg-black/80 px-1">Low Avoidance</span>
            <span class="absolute right-2 top-1/2 -translate-y-1/2 text-[9px] uppercase tracking-widest text-lime-600 rotate-90 origin-right bg-black/80 px-1">High Avoidance</span>
            <!-- Plot Point -->
            <div 
              class="absolute w-4 h-4 bg-white rounded-full -ml-2 -mt-2 shadow-[0_0_15px_#a3e635] transition-all duration-1000 ease-out"
              :style="{
                left: `${profile.ecr_r_scores.avoidance * 100}%`,
                top: `${(1 - profile.ecr_r_scores.anxiety) * 100}%`
              }"
            ></div>
          </div>
        </section>

        <!-- Qualitative Traits -->
        <section class="border-y border-lime-800 py-6 grid grid-cols-2 gap-4">
          <div>
            <span class="text-xs text-lime-600 uppercase tracking-wider block mb-1">Primary Love Language</span>
            <span class="text-sm text-white font-semibold">{{ profile.love_language }}</span>
          </div>
          <div>
            <span class="text-xs text-lime-600 uppercase tracking-wider block mb-1">Values Cluster</span>
            <span class="text-sm text-white font-semibold">{{ profile.values_cluster }}</span>
          </div>
          <div class="col-span-2 mt-4 pt-4 border-t border-lime-900/50">
            <span class="text-xs text-lime-600 uppercase tracking-wider block mb-1">Sociosexual Orientation</span>
            <span class="text-sm text-white font-semibold">{{ profile.sociosexual_orientation }}</span>
          </div>
        </section>

        <!-- Narrative -->
        <section class="border border-lime-800 p-6 bg-lime-900/10 relative overflow-hidden group">
          <div class="absolute inset-0 bg-lime-500/5 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"></div>
          <h2 class="text-xl mb-4 text-white uppercase tracking-widest flex justify-between items-center relative z-10">
            Agent Synthesis
            <button v-if="!profile.narrative && !generating" @click="generateNarrative" class="text-[10px] border border-lime-600 px-4 py-2 hover:bg-lime-900 hover:text-white text-lime-400 transition-all uppercase tracking-widest font-bold">Initiate</button>
            <span v-else-if="generating" class="text-[10px] text-lime-500 animate-pulse uppercase tracking-widest">Synthesizing...</span>
          </h2>
          
          <div v-if="profile.narrative" class="text-sm text-lime-300 space-y-4 leading-relaxed whitespace-pre-line relative z-10">
            {{ profile.narrative }}
          </div>
          <div v-else-if="generating" class="text-xs text-lime-700 font-mono italic leading-relaxed relative z-10">
            // Establishing LLM Handshake<br>
            // Cross-referencing ECR-R vectors with OCEAN signatures<br>
            // Injecting Spotify behavioral telemetry...<br>
            // Awaiting Anthropic synthesis...
          </div>
          <div v-else class="text-xs text-lime-700 italic relative z-10">
            No psychological synthesis available. Click Initiate to construct personalized narrative.
          </div>
        </section>

      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'

const profile = ref<any>(null)
const loading = ref(true)
const generating = ref(false)

const form = ref({
  O_score: 0.8,
  C_score: 0.6,
  E_score: 0.7,
  A_score: 0.8,
  N_score: 0.3,
  anxiety_score: 0.2,
  avoidance_score: 0.3,
  love_language: 'Quality Time',
  values_cluster: 'Progressive/Creative',
  sociosexual: 'Moderate'
})

const getHeaders = () => {
  const token = localStorage.getItem('channelzero-jwt')
  return { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }
}

onMounted(async () => {
  try {
    const res = await fetch('http://localhost:8000/api/psychometrics/profile', {
      headers: getHeaders()
    })
    if (res.ok) {
      profile.value = await res.json()
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})

const radarPoints = computed(() => {
  if (!profile.value || !profile.value.ipip_neo_scores) return ""
  // radius = 80, center = 100,100
  const scores = profile.value.ipip_neo_scores
  const o = scores.O * 80
  const c = scores.C * 80
  const e = scores.E * 80
  const a = scores.A * 80
  const n = scores.N * 80
  
  const p1 = `100,${100 - o}`
  const p2 = `${100 + Math.sin(72 * Math.PI/180) * c},${100 - Math.cos(72 * Math.PI/180) * c}`
  const p3 = `${100 + Math.sin(144 * Math.PI/180) * e},${100 - Math.cos(144 * Math.PI/180) * e}`
  const p4 = `${100 + Math.sin(216 * Math.PI/180) * a},${100 - Math.cos(216 * Math.PI/180) * a}`
  const p5 = `${100 + Math.sin(288 * Math.PI/180) * n},${100 - Math.cos(288 * Math.PI/180) * n}`
  
  return `${p1} ${p2} ${p3} ${p4} ${p5}`
})

const submitAssessment = async () => {
  try {
    const res = await fetch('http://localhost:8000/api/psychometrics/submit', {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ responses: form.value })
    })
    if (res.ok) {
      const data = await res.json()
      profile.value = data.profile
    }
  } catch (e) {
    console.error(e)
  }
}

const generateNarrative = async () => {
  generating.value = true
  try {
    const res = await fetch('http://localhost:8000/api/psychometrics/narrative', {
      method: 'POST',
      headers: getHeaders(),
    })
    if (res.ok) {
      const data = await res.json()
      profile.value.narrative = data.narrative
    } else {
      const err = await res.json()
      alert(err.detail || 'Error generating narrative. Do you have an API key set?')
    }
  } catch (e) {
    console.error(e)
  } finally {
    generating.value = false
  }
}
</script>

<style scoped>
input[type="number"]::-webkit-inner-spin-button,
input[type="number"]::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
input[type="number"] {
  -moz-appearance: textfield;
}
</style>
