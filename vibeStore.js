import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

export const useVibeStore = defineStore('vibe', () => {
  // --- State ---
  
  // Base User Identity (created after initial app signup/login)
  const user = ref({
    id: null,
    isAuthenticated: false,
    baseProfileCompleted: false, // Have they done the initial name/age setup?
  });

  // The Vibe Engine Data (populated via OAuth)
  const vibeData = ref({
    spotify: {
      connected: false,
      topArtists: [],
      audioFeatures: {}, // valence, danceability, etc.
      lastSync: null
    },
    twitter: {
      connected: false,
      linguisticProfile: null, // LLM generated summary
      engagementStyle: null,   // active, passive, argumentative
      lastSync: null
    },
    google: {
      connected: false,
      availabilityMatrix: [],  // Simplified calendar blocks
      lastSync: null
    }
  });

  // --- Getters ---
  
  // Is the user ready to enter the matching pool?
  const isMatchReady = computed(() => {
    // They MUST have Spotify connected at minimum
    return user.value.isAuthenticated && vibeData.value.spotify.connected;
  });

  // --- Actions ---

  // Handle the callback from an OAuth provider
  const processOAuthCallback = async (provider, authCode) => {
    try {
      // 1. Send authCode to our backend
      // const response = await api.post(`/auth/${provider}/callback`, { code: authCode });
      
      // 2. Backend exchanges code for tokens, fetches data, and processes it via LLM
      // const enrichedData = response.data;

      // Mocking the response for now
      console.log(`Processing ${provider} callback...`);
      
      vibeData.value[provider].connected = true;
      vibeData.value[provider].lastSync = new Date().toISOString();
      
      // We would map the enrichedData to our store state here
      
    } catch (error) {
      console.error(`Failed to process ${provider} OAuth:`, error);
      // Handle error state (e.g., show toast notification)
    }
  };

  const loginUser = (userData) => {
    user.value = { ...userData, isAuthenticated: true };
  };

  const logoutUser = () => {
    user.value = { id: null, isAuthenticated: false, baseProfileCompleted: false };
    // Reset vibe data to default state
  };

  return { user, vibeData, isMatchReady, processOAuthCallback, loginUser, logoutUser };
});