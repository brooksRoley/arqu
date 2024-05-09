<script setup lang="ts">
import MoodItem from './MoodItem.vue'
import HappyIcon from './icons/IconHappy.vue'
import SadIcon from './icons/IconSad.vue'
import AngryIcon from './icons/IconAngry.vue'
import CustomIcon from './icons/IconCustom.vue'
</script>

<template>
  <MoodItem>
    <template #icon><HappyIcon /></template>
    <template #heading>Feeling Happy</template>

    Feeling great today? Share your happiness with us!
  </MoodItem>

  <MoodItem>
    <template #icon><SadIcon /></template>
    <template #heading>Feeling Sad</template>

    Feeling down? Let us know what's bothering you.
  </MoodItem>

  <MoodItem>
    <template #icon><AngryIcon /></template>
    <template #heading>Feeling Angry</template>

    Mad at something? We're here to listen and support you.
  </MoodItem>

  <MoodItem>
    <template #icon><CustomIcon /></template>
    <template #heading>Custom Mood</template>

    Can't find your mood? Describe it in your own words.
  </MoodItem>
</template>
