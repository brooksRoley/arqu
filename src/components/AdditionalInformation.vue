<template>
  <div>
    <h2>Step 2: Additional Information</h2>
    <label for="additionalInfo">Additional Information:</label>
    <textarea id="additionalInfo" v-model="additionalInfo"></textarea>
    <button @click="prevStep">Back</button>
    <button @click="nextStep">Next</button>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref } from 'vue'

export default defineComponent({
  name: 'AdditionalInfo',
  props: {
    stepData: {
      type: Object,
      required: true
    }
  },
  setup(props, { emit }) {
    const additionalInfo = ref('')

    const prevStep = () => {
      emit('prev')
    }

    const nextStep = () => {
      emit('next', { additionalInfo: additionalInfo.value })
    }

    return {
      additionalInfo,
      prevStep,
      nextStep
    }
  }
})
</script>
