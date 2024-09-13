<template>
  <div class="wonka-factory">
    <h1 class="factory-title">Welcome to the Whimsical World of Data Confectionery!</h1>

    <p class="candy-text">
      Step into our marvelous Multi-Step Form Factory, where we craft personalized experiences
      sweeter than any Everlasting Gobstopper! Our Mood-o-Meter and Analysis Fudge-Packer work in
      tandem to create a parfait of perfection just for you!
    </p>

    <div class="button-box">
      <button @click="triggerChocolateRiver" class="wonka-button chocolate">
        Unleash the Chocolate River!
      </button>
      <button @click="triggerOompaLoompa" class="wonka-button oompa">Summon Oompa Loompas!</button>
      <button @click="triggerGoldenTicket" class="wonka-button golden">
        Find the Golden Ticket!
      </button>
    </div>

    <div class="animation-area">
      <div v-if="showChocolateRiver" class="chocolate-river"></div>
      <div v-if="showOompaLoompa" class="oompa-loompa"></div>
      <div v-if="showGoldenTicket" class="golden-ticket"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const showChocolateRiver = ref(false)
const showOompaLoompa = ref(false)
const showGoldenTicket = ref(false)

const triggerChocolateRiver = () => {
  showChocolateRiver.value = true
  setTimeout(() => {
    showChocolateRiver.value = false
  }, 3000)
}

const triggerOompaLoompa = () => {
  showOompaLoompa.value = true
  setTimeout(() => {
    showOompaLoompa.value = false
  }, 3000)
}

const triggerGoldenTicket = () => {
  showGoldenTicket.value = true
  setTimeout(() => {
    showGoldenTicket.value = false
  }, 3000)
}
</script>

<style scoped>
.wonka-factory {
  background-color: #f3e5ab;
  padding: 2rem;
  border-radius: 15px;
  box-shadow: 0 0 15px rgba(0, 0, 0, 0.1);
}

.factory-title {
  font-size: 2rem;
  color: #b8621b;
  text-align: center;
  margin-bottom: 1rem;
  font-family: 'Courier New', Courier, monospace;
}

.candy-text {
  font-size: 1.1rem;
  color: #3a1f04;
  line-height: 1.6;
  text-align: center;
  margin-bottom: 2rem;
}

.button-box {
  display: flex;
  justify-content: center;
  gap: 1rem;
  margin-bottom: 2rem;
}

.wonka-button {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 25px;
  font-size: 1rem;
  cursor: pointer;
  transition:
    transform 0.3s,
    box-shadow 0.3s;
}

.wonka-button:hover {
  transform: translateY(-3px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
}

.chocolate {
  background-color: #4b3621;
  color: #fff;
}
.oompa {
  background-color: #ff681f;
  color: #fff;
}
.golden {
  background-color: #ffd700;
  color: #000;
}

.animation-area {
  height: 200px;
  position: relative;
  overflow: hidden;
}

.chocolate-river {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 0;
  background-color: #4b3621;
  animation: flow 3s ease-out;
}

.oompa-loompa {
  width: 50px;
  height: 80px;
  background-color: #ff681f;
  border-radius: 50% 50% 0 0;
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  animation: dance 3s ease-in-out;
}

.golden-ticket {
  width: 100px;
  height: 60px;
  background-color: #ffd700;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation: shine 3s ease-in-out;
}

@keyframes flow {
  0% {
    height: 0;
  }
  100% {
    height: 100%;
  }
}

@keyframes dance {
  0%,
  100% {
    transform: translateX(-50%) rotate(0deg);
  }
  25% {
    transform: translateX(-150%) rotate(-15deg);
  }
  75% {
    transform: translateX(50%) rotate(15deg);
  }
}

@keyframes shine {
  0%,
  100% {
    opacity: 0;
    transform: translate(-50%, -50%) rotate(0deg);
  }
  50% {
    opacity: 1;
    transform: translate(-50%, -50%) rotate(360deg) scale(1.5);
  }
}
</style>
