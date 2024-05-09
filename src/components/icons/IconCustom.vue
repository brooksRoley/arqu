<template>
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
    <circle cx="12" cy="12" r="10" fill="#007bff" />
    <!-- Blue circle for the face -->
    <text
      x="50%"
      y="50%"
      text-anchor="middle"
      alignment-baseline="middle"
      font-size="16px"
      fill="#ffffff"
    >
      ?
    </text>
    <!-- Question mark -->
  </svg>
</template>

<script lang="ts">
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'CustomIcon'
})
</script>
