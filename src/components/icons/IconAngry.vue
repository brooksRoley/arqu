<template>
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
    <circle cx="12" cy="12" r="10" fill="#e74c3c" />
    <!-- Red circle for the face -->
    <circle cx="8" cy="10" r="1.5" fill="#231f20" />
    <!-- Left eye -->
    <circle cx="16" cy="10" r="1.5" fill="#231f20" />
    <!-- Right eye -->
    <path
      d="M10 15h4"
      fill="none"
      stroke="#231f20"
      stroke-linecap="round"
      stroke-linejoin="round"
      stroke-width="1.5"
    />
    <!-- Angry eyebrows -->
    <path
      d="M9 10h6"
      fill="none"
      stroke="#231f20"
      stroke-linecap="round"
      stroke-linejoin="round"
      stroke-width="1.5"
    />
    <!-- Angry mouth -->
  </svg>
</template>

<script lang="ts">
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'AngryIcon'
})
</script>
