<template>
  <div>
    <h2>Step 1: Select Your Mood</h2>
    <label v-for="(option, index) in moodOptions" :key="index">
      <input type="radio" :value="option.value" v-model="selectedMood" />
      {{ option.label }}
    </label>
    <input
      type="text"
      v-if="selectedMood === 'custom'"
      v-model="customMood"
      placeholder="Enter custom mood"
    />
    <button @click="nextStep">Next</button>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref } from 'vue'

export default defineComponent({
  name: 'MoodSelection',
  props: {
    stepData: {
      type: Object,
      required: true
    }
  },
  setup(props, { emit }) {
    const moodOptions = [
      { label: 'Fine', value: 'fine' },
      { label: 'Exuberant', value: 'exuberant' },
      { label: 'Seeking help', value: 'seeking-help' },
      { label: 'Custom', value: 'custom' }
    ]
    const selectedMood = ref('')
    const customMood = ref('')

    const nextStep = () => {
      if (selectedMood.value === 'custom') {
        // If custom mood is selected, use customMood value
        emit('next', { mood: customMood.value })
      } else {
        // Otherwise, use selectedMood value
        emit('next', { mood: selectedMood.value })
      }
    }

    return {
      moodOptions,
      selectedMood,
      customMood,
      nextStep
    }
  }
})
</script>
