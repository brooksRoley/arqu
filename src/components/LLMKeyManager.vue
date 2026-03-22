<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-xl font-bold text-purple-400">LLM Keys</h2>
        <p class="text-sm text-gray-500 mt-1">Bring your own key for Oracle synthesis. Your key is encrypted at rest.</p>
      </div>
    </div>

    <!-- Stored keys -->
    <div v-if="storedKeys.length" class="space-y-2">
      <div
        v-for="key in storedKeys"
        :key="key.id"
        class="flex items-center justify-between bg-gray-700/50 rounded-lg px-4 py-3"
      >
        <div class="flex items-center gap-3">
          <span class="text-sm font-semibold uppercase tracking-wider" :class="providerColor(key.provider)">
            {{ providerLabel(key.provider) }}
          </span>
          <span class="text-gray-500 text-xs font-mono">{{ key.key_hint }}</span>
        </div>
        <button
          @click="removeKey(key.id)"
          class="text-red-400/60 hover:text-red-400 text-xs font-medium transition-colors"
          :disabled="removing === key.id"
        >
          {{ removing === key.id ? '...' : 'REVOKE' }}
        </button>
      </div>
    </div>

    <!-- Add key form -->
    <div class="bg-gray-800/50 border border-gray-700 rounded-xl p-4 space-y-3">
      <div class="flex gap-3">
        <select
          v-model="selectedProvider"
          class="bg-gray-700 text-gray-200 rounded-lg px-3 py-2 text-sm border border-gray-600 focus:border-purple-500 focus:outline-none"
        >
          <option value="" disabled>Provider</option>
          <option v-for="p in availableProviders" :key="p.value" :value="p.value">
            {{ p.label }}
          </option>
        </select>
        <input
          v-model="keyInput"
          type="password"
          placeholder="Paste API key"
          class="flex-1 bg-gray-700 text-gray-200 rounded-lg px-3 py-2 text-sm border border-gray-600 focus:border-purple-500 focus:outline-none font-mono"
          @keyup.enter="storeKey"
        />
        <button
          @click="storeKey"
          :disabled="!selectedProvider || !keyInput.trim() || saving"
          class="bg-purple-600 hover:bg-purple-700 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold text-sm px-4 py-2 rounded-lg transition-colors"
        >
          {{ saving ? '...' : 'STORE' }}
        </button>
      </div>
      <p v-if="formError" class="text-red-400 text-xs">{{ formError }}</p>
      <p class="text-gray-600 text-xs">
        Keys are encrypted with AES-256-GCM before storage. Plaintext only exists in memory during synthesis.
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/composables/useAuthStore'

interface StoredKey {
  id: string
  provider: string
  key_hint: string
}

const PROVIDERS = [
  { value: 'openai', label: 'OpenAI', color: 'text-green-400' },
  { value: 'anthropic', label: 'Anthropic (Claude)', color: 'text-orange-400' },
  { value: 'google', label: 'Google (Gemini)', color: 'text-blue-400' },
  { value: 'xai', label: 'xAI (Grok)', color: 'text-gray-300' },
  { value: 'together', label: 'Together', color: 'text-cyan-400' },
]

const { apiFetch } = useAuthStore()

const storedKeys = ref<StoredKey[]>([])
const selectedProvider = ref('')
const keyInput = ref('')
const saving = ref(false)
const removing = ref<string | null>(null)
const formError = ref<string | null>(null)

const availableProviders = PROVIDERS

function providerLabel(p: string) {
  return PROVIDERS.find(x => x.value === p)?.label ?? p
}

function providerColor(p: string) {
  return PROVIDERS.find(x => x.value === p)?.color ?? 'text-gray-400'
}

async function fetchKeys() {
  try {
    storedKeys.value = await apiFetch<StoredKey[]>('/api/llm/keys')
  } catch {
    // silent — keys section just stays empty
  }
}

async function storeKey() {
  if (!selectedProvider.value || !keyInput.value.trim()) return
  saving.value = true
  formError.value = null
  try {
    await apiFetch<StoredKey>('/api/llm/keys', {
      method: 'POST',
      body: JSON.stringify({
        provider: selectedProvider.value,
        api_key: keyInput.value.trim(),
      }),
    })
    keyInput.value = ''
    selectedProvider.value = ''
    await fetchKeys()
  } catch (e: any) {
    formError.value = e.message
  } finally {
    saving.value = false
  }
}

async function removeKey(id: string) {
  removing.value = id
  try {
    await apiFetch(`/api/llm/keys/${id}`, { method: 'DELETE' })
    storedKeys.value = storedKeys.value.filter(k => k.id !== id)
  } catch {
    // silent
  } finally {
    removing.value = null
  }
}

onMounted(fetchKeys)
</script>
