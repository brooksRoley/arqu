<template>
  <div class="mood-item">
    <div class="mood-icon">
      <slot name="icon"></slot>
    </div>
    <div class="mood-content">
      <h3 class="mood-heading">
        <slot name="heading"></slot>
      </h3>
      <p class="mood-description">
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

<style scoped>
.mood-item {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}

.mood-icon {
  margin-right: 20px;
}

.mood-heading {
  margin: 0;
  font-size: 18px;
  font-weight: bold;
}

.mood-description {
  margin: 0;
  font-size: 16px;
}
</style>
