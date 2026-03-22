<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/composables/useAuthStore'

const router = useRouter()
const { login, register, loading, error, isAuthenticated } = useAuthStore()

// If already logged in, redirect
if (isAuthenticated.value) {
  router.replace('/')
}

const mode = ref<'login' | 'register'>('login')
const email = ref('')
const password = ref('')
const displayName = ref('')
const localError = ref('')

const formValid = computed(() => {
  if (!email.value.trim() || !password.value) return false
  if (mode.value === 'register' && password.value.length < 8) return false
  return true
})

async function submit() {
  localError.value = ''
  try {
    if (mode.value === 'login') {
      await login(email.value.trim(), password.value)
    } else {
      await register(email.value.trim(), password.value, displayName.value.trim() || undefined)
    }
    router.push('/')
  } catch (e: any) {
    localError.value = e.message || 'Something went wrong'
  }
}

function toggleMode() {
  mode.value = mode.value === 'login' ? 'register' : 'login'
  localError.value = ''
}
</script>

<template>
  <div class="login-wrap">
    <div class="login-card">
      <h1 class="login-title">Channel Zero</h1>
      <p class="login-subtitle">{{ mode === 'login' ? 'Sign in to continue' : 'Create your account' }}</p>

      <form @submit.prevent="submit" class="login-form">
        <input
          v-if="mode === 'register'"
          v-model="displayName"
          type="text"
          placeholder="Display name (optional)"
          class="login-input"
          autocomplete="name"
        />

        <input
          v-model="email"
          type="email"
          placeholder="Email"
          class="login-input"
          autocomplete="email"
          required
        />

        <input
          v-model="password"
          type="password"
          :placeholder="mode === 'register' ? 'Password (8+ characters)' : 'Password'"
          class="login-input"
          autocomplete="current-password"
          required
        />

        <p v-if="localError || error" class="login-error">{{ localError || error }}</p>

        <button
          type="submit"
          class="login-btn"
          :disabled="!formValid || loading"
        >
          {{ loading ? '...' : mode === 'login' ? 'Sign In' : 'Create Account' }}
        </button>
      </form>

      <button class="toggle-btn" @click="toggleMode">
        {{ mode === 'login' ? "Don't have an account? Sign up" : 'Already have an account? Sign in' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.login-wrap {
  min-height: calc(100vh - 3rem);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem 1rem;
}

.login-card {
  width: 100%;
  max-width: 400px;
  background: rgba(20, 20, 40, 0.85);
  border: 1px solid rgba(100, 100, 255, 0.18);
  border-radius: 1rem;
  padding: 2.5rem 2rem;
  backdrop-filter: blur(12px);
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.25rem;
}

.login-title {
  font-size: 1.6rem;
  font-weight: 700;
  color: #e2e8f0;
  margin: 0;
  background: linear-gradient(135deg, #c4b5fd, #818cf8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.login-subtitle {
  font-size: 0.82rem;
  color: #64748b;
  margin: 0;
}

.login-form {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.login-input {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 0.5rem;
  background: rgba(0, 0, 0, 0.3);
  color: #e2e8f0;
  font-family: inherit;
  font-size: 0.88rem;
  outline: none;
  transition: border-color 0.15s;
  box-sizing: border-box;
}

.login-input:focus {
  border-color: rgba(99, 102, 241, 0.5);
}

.login-input::placeholder {
  color: #475569;
}

.login-error {
  font-size: 0.78rem;
  color: #f87171;
  margin: 0;
  text-align: center;
}

.login-btn {
  width: 100%;
  padding: 0.75rem;
  border: none;
  border-radius: 0.5rem;
  background: linear-gradient(135deg, #6366f1, #7c3aed);
  color: #fff;
  font-size: 0.9rem;
  font-weight: 600;
  font-family: inherit;
  cursor: pointer;
  transition: opacity 0.15s, transform 0.1s;
}

.login-btn:hover:not(:disabled) {
  opacity: 0.9;
  transform: translateY(-1px);
}

.login-btn:disabled {
  opacity: 0.4;
  cursor: default;
}

.toggle-btn {
  background: none;
  border: none;
  color: #64748b;
  font-size: 0.78rem;
  font-family: inherit;
  cursor: pointer;
  padding: 0.3rem 0;
  transition: color 0.15s;
}

.toggle-btn:hover {
  color: #a5b4fc;
}

@media (max-width: 480px) {
  .login-card {
    padding: 2rem 1.25rem;
  }
}
</style>
