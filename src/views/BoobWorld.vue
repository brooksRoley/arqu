<template>
  <div @click="handleClick" class="jiggle-button">
    <svg
      id="boob-icon"
      width="200"
      height="200"
      viewBox="0 0 200 200"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <circle class="outer-circle" cx="50" cy="100" r="50" fill="#FF69B4" />
      <circle class="nipple" cx="50" cy="100" r="10" fill="#FF1493" />
      <circle class="outer-circle" cx="150" cy="100" r="50" fill="#FF69B4" />
      <circle class="nipple" cx="150" cy="100" r="10" fill="#FF1493" />
    </svg>
  </div>
</template>

<script setup>
import { ref } from 'vue'

// State to track the click animation
const isClicked = ref(false)

const handleClick = () => {
  isClicked.value = true
  setTimeout(() => {
    isClicked.value = false
  }, 500)
}
</script>

<style scoped>
/* Jiggle Button Styling */
.jiggle-button {
  cursor: pointer;
  display: inline-block;
  margin-top: 20px;
  animation: jiggle-animation 2s infinite;
}

/* Circle Animations */
.outer-circle {
  animation: circle-jiggle 0.5s ease-in-out infinite alternate;
}

.nipple {
  animation: nipple-jiggle 0.5s ease-in-out infinite alternate;
}

/* Jiggle Animations */
@keyframes circle-jiggle {
  0% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-5px);
  }
  100% {
    transform: translateY(0px);
  }
}

@keyframes nipple-jiggle {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
  100% {
    transform: scale(1);
  }
}

@keyframes jiggle-animation {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05) rotate(2deg);
  }
}

/* Hover Effect */
.jiggle-button:hover {
  animation: bounce 0.3s;
}

/* Click Animation Effect */
.jiggle-button:active {
  animation: jiggle-on-click 0.5s ease;
}

@keyframes bounce {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
  100% {
    transform: scale(1);
  }
}

@keyframes jiggle-on-click {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.15) rotate(2deg);
  }
}
</style>
