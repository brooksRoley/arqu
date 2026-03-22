<template>
  <div class="min-h-screen bg-black text-gray-200 p-6 flex flex-col md:flex-row gap-8">
    
    <div class="w-full md:w-1/2 space-y-6">
      <h1 class="text-3xl font-extrabold text-white tracking-widest uppercase border-b border-gray-800 pb-4">
        Nightly Yield: 3/3
      </h1>
      
      <div class="bg-gray-900 border border-gray-700 rounded-xl p-6 relative overflow-hidden">
        <div class="absolute top-0 left-0 w-1 h-full bg-purple-600"></div>
        
        <div class="flex justify-between items-start">
          <div>
            <h2 class="text-2xl font-bold text-white">{{ match.name }}</h2>
            <p class="text-gray-500 text-sm">94% Vibe Alignment</p>
          </div>
          <button @click="initiateChat(match.id)" class="bg-purple-600 hover:bg-purple-500 text-white px-4 py-2 rounded font-bold text-sm transition-colors">
            Initiate Contact
          </button>
        </div>

        <div class="mt-6 flex gap-4">
          <img :src="`data:image/png;base64,${match.graph_overlay}`" alt="Compatibility Graph" class="w-32 h-32 object-contain" />
          
          <div class="space-y-2 text-sm text-gray-400 flex-1">
            <p><strong class="text-gray-200">Sonic Overlap:</strong> You both hyper-fixate on aggressive 90s shoegaze and high-tempo ambient. His valence is similarly depressive.</p>
            <p><strong class="text-gray-200">Neurotic Footprint:</strong> Match shows high linguistic dominance and dark humor on X. Algorithm suggests he pays for the first round.</p>
            <p><strong class="text-gray-200">Logistics:</strong> Neon DB queries confirm you both have Thursday at 8 PM open. A comedy cellar 3 miles away is suggested.</p>
          </div>
        </div>
      </div>
    </div>

    <div class="w-full md:w-1/2 bg-gray-900 border border-gray-800 rounded-xl flex flex-col h-[85vh]">
      <div class="p-4 border-b border-gray-800 bg-gray-950 rounded-t-xl">
        <h3 class="text-lg font-bold text-white flex items-center gap-2">
          <span class="w-2 h-2 rounded-full bg-green-500"></span> Vibe Oracle (Internal Journal)
        </h3>
        <p class="text-xs text-gray-500">Process your results with your algorithm before speaking to them.</p>
      </div>
      
      <div class="flex-1 p-4 overflow-y-auto space-y-4 font-mono text-sm" ref="journalScroll">
        <div v-for="msg in journalLog" :key="msg.id" :class="msg.role === 'user' ? 'text-blue-400 text-right' : 'text-purple-400 text-left'">
          <span class="block text-xs text-gray-600 mb-1">{{ msg.role === 'user' ? 'You' : 'Oracle' }}</span>
          <p class="bg-gray-800 inline-block p-3 rounded-lg max-w-[85%]">{{ msg.content }}</p>
        </div>
      </div>

      <div class="p-4 border-t border-gray-800">
        <input 
          v-model="journalInput" 
          @keyup.enter="sendToOracle"
          type="text" 
          placeholder="Why did it match me with Cassian?" 
          class="w-full bg-black border border-gray-700 text-white p-3 rounded focus:outline-none focus:border-purple-500 transition-colors"
        />
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref } from 'vue';

// Mock data pulled from Neon Serverless DB
const match = ref({
  id: 'usr_8829',
  name: 'Cassian Vance',
  graph_overlay: 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=' // Placeholder Base64
});

const journalInput = ref('');
const journalLog = ref([
  { id: 1, role: 'oracle', content: 'Nightly batch processed. You matched with Cassian at 94%. What are your initial thoughts on his matrix?' },
  { id: 2, role: 'user', content: 'He listens to the exact same sad indie playlist I do, but his Twitter data says he is highly dominant. Isn\'t that a contradiction?' },
  { id: 3, role: 'oracle', content: 'Not at all. The LLM parsed his tweets. He uses melancholy audio to self-regulate, but his social interactions are highly assertive and decisive. This perfectly complements your indecisive booking habits. He will pick the venue. You will simply show up.' }
]);

const sendToOracle = async () => {
  if (!journalInput.value) return;
  
  journalLog.value.push({ id: Date.now(), role: 'user', content: journalInput.value });
  const query = journalInput.value;
  journalInput.value = '';

  // Here, we hit our FastAPI backend, which queries the Neon DB for the user's vector, 
  // Cassian's vector, and feeds them into Claude to generate the Oracle's response.
  setTimeout(() => {
    journalLog.value.push({
      id: Date.now() + 1,
      role: 'oracle',
      content: `If you look at his calendar API overlap, you'll see he rarely commits to weekends. Thursday is your only window. The algorithm suggests he is emotionally guarded but physically available. Do you want me to draft the opening message based on his heavy rotation of Deftones?`
    });
  }, 1000);
};

const initiateChat = (id) => {
  console.log(`Connecting to Neon DB Websocket for chat room with ${id}`);
};
</script>