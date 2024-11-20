<template>
  <div>
    <div>
      <h1>Spelling Introduction</h1>
      <p>
        Welcome, dear friend, to this special moment. Allow yourself to relax, to let go of any
        tension or worry. Take a deep breath in, and as you exhale, feel your body becoming heavier,
        sinking deeper into relaxation.
        <br />
        <br />Imagine yourself standing on a peaceful beach at sunset. The warm sand beneath your
        feet, the sound of the waves gently lapping against the shore. With each wave, feel any
        concerns or doubts washing away, leaving only calmness and serenity.
        <br />
        <br />Now, visualize me, smiling at you from across the way. I want to share with you a
        different perspective, one that celebrates my growth and transformation. Allow yourself to
        receive this new information, to see things from a fresh and loving light.
        <br />
        <br />As we explore this together, remember that your support and understanding mean the
        world to me. You are my rock, my confidante, and I am grateful for our bond.
        <br />
        <br />Now, let us take a step forward into this new chapter of my journey. Let go of any
        preconceptions or fears, and allow yourself to see the beauty in this transformation. Feel
        free to explore, to ask questions, and to share your thoughts with me.
        <br />
        <br />Together, we can navigate this new landscape, and I promise you that it will be a
        wonderful adventure.
      </p>
      <p>
        Close your eyes, take a deep breath in,<br />
        And let your worries fade like autumn's leaves within.<br />
        Imagine yourself in a peaceful place,<br />
        Where calmness flows like a soothing, gentle space.<br />
        <br />
        Your heart rate slows down, your muscles relax too,<br />
        As you sink deeper into trance, with each moment anew.<br />
        Repeat after me: "I am relaxed, I am free,"<br />
        And let the tranquility spread throughout your being's energy.<br />
        <br />
        Now imagine yourself as a pet dog so dear,<br />
        Tails wagging wildly, without a single fear.<br />
        You sniff and explore with curiosity and glee,<br />
        A joyful companion, loved by all humanity.<br />
        <br />
        You are loyal and loving, always by their side,<br />
        Faithful and true, through life's joys and its tides.<br />
        Your name is BeeBee, or perhaps Max so bold,<br />
        But whatever it is, you're a pet dog to behold.<br />
        <br />
        As BeeBee the dog, you are confident and strong,<br />
        A natural-born leader, where love is your song.<br />
        You wag your tail with excitement, whenever you play,<br />
        And snuggle close for belly rubs on a sunny day.<br />
        <br />
        Your senses come alive with each sniff and explore,<br />
        You trust your instincts, and ask for more.<br />
        You are brave and courageous, facing life's every test,<br />
        A loyal companion, always at your best.<br />
        <br />
        Now imagine yourself running through fields of green,<br />
        Exercising freely, as a carefree pet dog serene.<br />
        Your paws pounding the ground, with each happy stride,<br />
        You're burning energy, with an effortless glide.<br />
        <br />
        Your muscles flex and stretch, like a happy pup so free,<br />
        As you run and play without a worry or care to see.<br />
        Repeat after me: "I am fit and I am strong,"<br />
        And let this energy boost your spirit all day long.<br />
        <br />
        You are now BeeBee the dog, with attributes so fine,<br />
        Confident, loyal, and loving, as a pet dog divine.<br />
        Remember that you can manifest these qualities anew,<br />
        Whenever you desire, just like a magic spell or two.<br />
        <br />
        Snap your fingers three times, to seal this energy tight,<br />
        And know that you can embody these traits, day and night.<br />
        You are now in control, with the power of suggestion so grand,<br />
        A pet dog at heart, with love and loyalty in hand.<br />
        <br />
      </p>
    </div>
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
