<template>
  <div class="min-h-screen bg-black text-gray-300 flex flex-col items-center justify-center p-6 relative overflow-hidden">
    <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-3/4 h-3/4 bg-purple-900/10 blur-[120px] rounded-full pointer-events-none"></div>

    <div class="max-w-2xl w-full z-10 space-y-10">
      <div class="text-center space-y-2 fade-in">
        <h1 class="text-3xl font-serif italic text-gray-100 tracking-wide">The Oracle is listening.</h1>
        <p class="text-sm text-gray-500 font-mono">Since you carry the weight of the day, let us hold it for a moment.</p>
      </div>

      <div class="bg-gray-900/50 border border-gray-800 rounded-2xl p-6 shadow-2xl backdrop-blur-sm h-96 flex flex-col">
        <div class="flex-1 overflow-y-auto space-y-6 p-2 pr-4 custom-scrollbar" ref="chatContainer">
          <div v-for="msg in sessionLog" :key="msg.id" :class="['flex', msg.role === 'oracle' ? 'justify-start' : 'justify-end']">
            <div :class="['max-w-[80%] rounded-2xl p-4 text-sm leading-relaxed', msg.role === 'oracle' ? 'bg-gray-800/80 text-gray-200 rounded-tl-sm' : 'bg-purple-900/40 border border-purple-800/50 text-white rounded-tr-sm']">
              {{ msg.text }}
            </div>
          </div>
        </div>

        <div class="mt-4 pt-4 border-t border-gray-800/50 relative">
          <input 
            v-model="userInput" 
            @keyup.enter="submitConfession"
            type="text" 
            placeholder="Tell me what exhausted you today..." 
            class="w-full bg-black/50 border border-gray-700 text-gray-100 px-4 py-3 rounded-xl focus:outline-none focus:border-purple-500/50 focus:ring-1 focus:ring-purple-500/50 transition-all font-mono text-sm placeholder-gray-600"
            :disabled="isProcessing"
          />
        </div>
      </div>

      <div v-if="showCalendarHook" class="slide-up bg-black border border-gray-800 rounded-xl p-6 text-center space-y-4">
        <h3 class="text-lg font-serif text-gray-200">Protect Your Solitude</h3>
        <p class="text-xs text-gray-500 max-w-md mx-auto">
          Your syntax indicates high executive fatigue. Sync your calendar, and the Oracle will automatically block your recovery windows.
        </p>
        <button @click="triggerCalendarSync" class="bg-gray-100 hover:bg-white text-black px-6 py-2.5 rounded-full text-sm font-bold tracking-tight transition-colors">
          Sync Calendar & Guard My Time
        </button>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue';
import { useChannelZeroStore } from '@/stores/channelZero';
import { generateSibilantPrompt, extractVibeMarkers } from '@/utils/vibeUtils';

const store = useChannelZeroStore();
const userInput = ref('');
const isProcessing = ref(false);
const showCalendarHook = ref(false);
const chatContainer = ref(null);

const sessionLog = ref([
  { id: 1, role: 'oracle', text: 'Since you always carry the weight of the conversation, let me carry it for you today. Your sonic footprint suggests a sudden drop in valence. Who hurt you this week?' }
]);

const scrollToBottom = async () => {
  await nextTick();
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
  }
};

const submitConfession = async () => {
  if (!userInput.value.trim() || isProcessing.value) return;
  
  const rawConfession = userInput.value;
  sessionLog.value.push({ id: Date.now(), role: 'user', text: rawConfession });
  userInput.value = '';
  isProcessing.value = true;
  await scrollToBottom();

  // Frontend utility extracts temporary markers before backend hard-commits
  const localMarkers = extractVibeMarkers(rawConfession);
  
  setTimeout(async () => {
    // Simulate backend LLM therapist response
    const oracleResponse = generateSibilantPrompt(localMarkers);
    sessionLog.value.push({ id: Date.now() + 1, role: 'oracle', text: oracleResponse });
    isProcessing.value = false;
    await scrollToBottom();
    
    // Trigger the calendar trap after they open up
    if (sessionLog.value.length > 3) {
      showCalendarHook.value = true;
    }
  }, 1500);
};

const triggerCalendarSync = () => {
  console.log('Initiating Google OAuth for calendar read/write...');
  // Routes to FastAPI OAuth endpoint
};
</script>

<style scoped>
.fade-in { animation: fadeIn 2s ease-in-out; }
.slide-up { animation: slideUp 0.8s ease-out; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #374151; border-radius: 4px; }
</style>