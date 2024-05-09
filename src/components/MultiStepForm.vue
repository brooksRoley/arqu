<template>
  <div>
    <component
      :is="currentStep.component"
      :step-data="currentStepData"
      @next="nextStep"
      @prev="prevStep"
      @submit="submitForm"
    />
  </div>
</template>

<script lang="ts">
import { defineComponent, ref } from 'vue'
import MoodSelection from './MoodSelection.vue'
import AdditionalInformation from './AdditionalInformation.vue'
import Confirmation from './Confirmation.vue'

export default defineComponent({
  name: 'MultiStepForm',
  components: {
    MoodSelection,
    AdditionalInformation,
    Confirmation
  },
  setup() {
    const steps = [
      { component: 'MoodSelection', data: null },
      { component: 'AdditionalInformation', data: null },
      { component: 'Confirmation', data: null }
    ]
    const currentStepIndex = ref(0)

    const currentStepData = ref<any>(null)

    const currentStep = ref(steps[currentStepIndex.value])

    const nextStep = () => {
      currentStepIndex.value++
      currentStep.value = steps[currentStepIndex.value]
    }

    const prevStep = () => {
      currentStepIndex.value--
      currentStep.value = steps[currentStepIndex.value]
    }

    const submitForm = (formData: any) => {
      // Here you can handle the form submission, e.g., send data to server
      console.log('Form data submitted:', formData)
      alert('Form submitted successfully!')
    }

    return {
      currentStep,
      currentStepData,
      nextStep,
      prevStep,
      submitForm
    }
  }
})
</script>
