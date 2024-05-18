<template>
  <div>
    <component
      :is="currentStep.component"
      :stepData="currentStepData"
      @next="nextStep"
      @prev="prevStep"
      @submit="submitForm"
    />
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed } from 'vue'
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
    const currentStep = computed(() => steps[currentStepIndex.value])
    const currentStepData = ref({})

    const nextStep = () => {
      currentStepIndex.value++
      console.log(steps[currentStepIndex.value].data)
      currentStep.value = steps[currentStepIndex.value]
    }

    const prevStep = () => {
      currentStepIndex.value--
      currentStep.value = steps[currentStepIndex.value]
    }

    const submitForm = (formData: any) => {
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
