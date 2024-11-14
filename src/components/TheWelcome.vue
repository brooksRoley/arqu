<script setup lang="ts">
import MoodItem from './MoodItem.vue'
import HappyIcon from './icons/IconHappy.vue'
import SadIcon from './icons/IconSad.vue'
import AngryIcon from './icons/IconAngry.vue'
import CustomIcon from './icons/IconCustom.vue'
</script>

<template>
  <h1>Hypnotic Induction Script</h1>
  <p>
    Welcome, dear friend, to this special moment. Allow yourself to relax, to let go of any tension
    or worry. Take a deep breath in, and as you exhale, feel your body becoming heavier, sinking
    deeper into relaxation.
  </p>
  <p>
    Imagine yourself standing on a peaceful beach at sunset. The warm sand beneath your feet, the
    sound of the waves gently lapping against the shore. With each wave, feel any concerns or doubts
    washing away, leaving only calmness and serenity.
  </p>
  <p>
    Now, visualize me, smiling at you from across the way. I want to share with you a different
    perspective, one that celebrates my growth and transformation. Allow yourself to receive this
    new information, to see things from a fresh and loving light.
  </p>
  <p>
    As we explore this together, remember that your support and understanding mean the world to me.
    You are my rock, my confidante, and I am grateful for our bond.
  </p>
  <p>
    Now, let us take a step forward into this new chapter of my journey. Let go of any
    preconceptions or fears, and allow yourself to see the beauty in this transformation. Feel free
    to explore, to ask questions, and to share your thoughts with me.
  </p>
  <p>
    Together, we can navigate this new landscape, and I promise you that it will be a wonderful
    adventure.
  </p>
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
