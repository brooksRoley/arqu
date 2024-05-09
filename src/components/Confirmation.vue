<template>
  <div>
    <h2>Step 3: Confirmation</h2>
    <p>Review your selections:</p>
    <ul>
      <li v-for="(value, key) in stepData" :key="key">{{ key }}: {{ value }}</li>
    </ul>
    <button @click="prevStep">Back</button>
    <button @click="submitForm">Submit</button>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'Confirmation',
  props: {
    stepData: {
      type: Object,
      required: true
    }
  },
  setup(props, { emit }) {
    const prevStep = () => {
      emit('prev')
    }

    const submitForm = () => {
      emit('submit', props.stepData)
    }

    return {
      prevStep,
      submitForm
    }
  }
})
</script>
