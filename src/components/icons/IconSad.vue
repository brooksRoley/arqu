<template>
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
    <circle cx="12" cy="12" r="10" fill="#6c757d" />
    <!-- Gray circle for the face -->
    <circle cx="8" cy="10" r="1.5" fill="#231f20" />
    <!-- Left eye -->
    <circle cx="16" cy="10" r="1.5" fill="#231f20" />
    <!-- Right eye -->
    <path
      d="M15.5 16.5c-.97-.97-2.26-1.5-3.5-1.5s-2.53.53-3.5 1.5"
      fill="none"
      stroke="#231f20"
      stroke-linecap="round"
      stroke-linejoin="round"
      stroke-width="1.5"
    />
    <!-- Mouth -->
  </svg>
</template>

<script lang="ts">
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'SadIcon'
})
</script>
