<template>
  <div>
    <component
      :is="currentStep.component"
      :stepData="currentStepData"
      @next="nextStep"
      @prev="prevStep"
      @submit="submitForm"
      @updateData="updateStepData"
    />
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed } from 'vue'
import MoodSelection from './MoodSelection.vue'
import AdditionalInformation from './AdditionalInformation.vue'
import Confirmation from './Confirmation.vue'

interface Step {
  component: string
  data: Record<string, any> | null
}

interface FormData {
  mood?: string
  additionalInfo?: string
  // Add more fields as needed
}

export default defineComponent({
  name: 'MultiStepForm',
  components: {
    MoodSelection,
    AdditionalInformation,
    Confirmation
  },
  setup() {
    const steps: Step[] = [
      { component: 'MoodSelection', data: null },
      { component: 'AdditionalInformation', data: null },
      { component: 'Confirmation', data: null }
    ]
    const currentStepIndex = ref(0)
    const currentStep = computed(() => steps[currentStepIndex.value])
    const formData = ref<FormData>({})

    const currentStepData = computed(() => ({
      ...formData.value,
      ...steps[currentStepIndex.value].data
    }))

    const nextStep = () => {
      if (currentStepIndex.value < steps.length - 1) {
        currentStepIndex.value++
      }
    }

    const prevStep = () => {
      if (currentStepIndex.value > 0) {
        currentStepIndex.value--
      }
    }

    const updateStepData = (newData: Partial<FormData>) => {
      formData.value = { ...formData.value, ...newData }
    }

    const submitForm = () => {
      try {
        // Perform any final validation here
        if (!formData.value.mood) {
          throw new Error('Mood selection is required')
        }
        console.log('Form data submitted:', formData.value)
        alert('Form submitted successfully!')
        // Reset form after successful submission
        formData.value = {}
        currentStepIndex.value = 0
      } catch (error) {
        if (error instanceof Error) {
          alert(`Form submission failed: ${error.message}`)
        } else {
          alert('An unknown error occurred')
        }
      }
    }

    return {
      currentStep,
      currentStepData,
      nextStep,
      prevStep,
      updateStepData,
      submitForm
    }
  }
})
</script>
