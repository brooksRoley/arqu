<template>
  <div class="flex items-center mb-8 text-lg">
    <div class="mr-4">
      <slot name="icon"></slot>
    </div>
    <div class="mood-content">
      <h3>
        <slot name="heading"></slot>
      </h3>
      <p class="m-0">
        <slot></slot>
      </p>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'MoodItem'
})
</script>
