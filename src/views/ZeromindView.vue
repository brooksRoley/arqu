<script setup lang="ts">
import { ref, watch } from 'vue'
import { useStoryStore } from '@/composables/useStoryStore'

const { currentWord } = useStoryStore()
const iframeRef = ref<HTMLIFrameElement | null>(null)
let iframeReady = false

function onIframeLoad() {
  iframeReady = true
  sendWord(currentWord.value)
}

function sendWord(word: string) {
  if (iframeReady && iframeRef.value?.contentWindow) {
    iframeRef.value.contentWindow.postMessage({ type: 'wordUpdate', word }, '*')
  }
}

watch(currentWord, (word) => {
  sendWord(word)
})
</script>

<template>
  <iframe
    ref="iframeRef"
    src="/generative-background.html"
    class="full-frame"
    @load="onIframeLoad"
  />
</template>

<style scoped>
.full-frame {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border: none;
}
</style>
