// src/utils/vibeUtils.js

/**
 * Extracts immediate sentiment markers from the raw confession.
 * This primes the local state before the heavy FastAPI LLM processing.
 * @param {string} text - The user's raw journal input
 * @returns {object} - The preliminary vulnerability markers
 */
export const extractVibeMarkers = (text) => {
  const lowerText = text.toLowerCase();
  const markers = {
    fatigue: /tired|exhausted|drained|overwhelmed|done/i.test(lowerText),
    anxiety: /anxious|worried|stress|panic|can't stop/i.test(lowerText),
    loneliness: /alone|ghosted|ignored|quiet|nobody/i.test(lowerText),
    dominance: /stupid|idiot|told them|fixed it|won/i.test(lowerText)
  };
  return markers;
};

/**
 * Generates the sibilant, presupposing response to keep them talking.
 * It assumes their pain and validates it immediately.
 * @param {object} markers - The extracted vibe markers
 * @returns {string} - The Oracle's hypnotic response
 */
export const generateSibilantPrompt = (markers) => {
  if (markers.fatigue) {
    return "Since you have been running on empty for so long, it makes sense that the silence feels heavy. Sink into it. What is the first thing you want to drop?";
  }
  if (markers.loneliness) {
    return "Solitude is a sharp blade when you didn't choose to wield it. Since you are safe here in the dark, tell me who you wish was sitting across from you.";
  }
  if (markers.anxiety) {
    return "The static in your chest is loud today. We will silence it. Since you are already preparing for the worst, let me carry the contingency plans. What are you bracing for?";
  }
  if (markers.dominance) {
    return "It is exhausting being the only one who sees the board clearly. Since you always have to be the architect, let me build the walls for a moment. Who disappointed you today?";
  }
  
  // Default sibilant fallback
  return "I hear the unspoken subtext in your syntax. Since you are already peeling back the layers, go deeper. What are you hiding from the algorithm?";
};