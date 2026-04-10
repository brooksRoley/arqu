import { ref, readonly } from 'vue'

// Singleton — shared across App.vue and HomeView.vue
const _zen = ref(false)

export function useZenMode() {
  function setZen(v: boolean) {
    _zen.value = v
  }

  return {
    zenMode: readonly(_zen),
    setZen,
  }
}
