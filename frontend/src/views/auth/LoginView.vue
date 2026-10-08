<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const form = reactive({
  email: '',
  password: '',
})
const error = ref<string | null>(null)

async function handleLogin() {
  error.value = null
  try {
    await authStore.login(form.email, form.password)
    router.push({ name: 'dashboard' })
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string } } }
    error.value = e?.response?.data?.detail ?? 'Login failed. Please try again.'
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-card__header">
        <span class="auth-logo">🧩</span>
        <h1 class="auth-title">MockEase</h1>
        <p class="auth-subtitle">Sign in to your account</p>
      </div>

      <form class="auth-form" @submit.prevent="handleLogin">
        <div class="form-group">
          <label class="form-label">Email</label>
          <input
            v-model="form.email"
            type="email"
            class="form-input"
            placeholder="you@example.com"
            required
            autocomplete="email"
          />
        </div>

        <div class="form-group">
          <label class="form-label">Password</label>
          <input
            v-model="form.password"
            type="password"
            class="form-input"
            placeholder="••••••••"
            required
            autocomplete="current-password"
          />
        </div>

        <div v-if="error" class="auth-error">
          {{ error }}
        </div>

        <button type="submit" class="btn btn--primary btn--full" :disabled="authStore.loading">
          {{ authStore.loading ? 'Signing in…' : 'Sign in' }}
        </button>
      </form>

      <p class="auth-footer">
        Don't have an account?
        <RouterLink to="/register" class="auth-link">Create one</RouterLink>
      </p>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: #0f0f11;
  padding: 1rem;
}

.auth-card {
  width: 100%;
  max-width: 400px;
  background: #18181c;
  border: 1px solid #2a2a35;
  border-radius: 12px;
  padding: 2rem;
}

.auth-card__header {
  text-align: center;
  margin-bottom: 1.75rem;
}

.auth-logo {
  font-size: 2rem;
  display: block;
  margin-bottom: 0.5rem;
}

.auth-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #a78bfa;
  margin: 0 0 0.25rem;
}

.auth-subtitle {
  font-size: 0.875rem;
  color: #6666a0;
  margin: 0;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.form-label {
  font-size: 0.8125rem;
  font-weight: 500;
  color: #9999b3;
}

.form-input {
  padding: 0.625rem 0.875rem;
  background: #0f0f11;
  border: 1px solid #2a2a35;
  border-radius: 8px;
  color: #e8e8f0;
  font-size: 0.9375rem;
  outline: none;
  transition: border-color 0.15s;
}

.form-input:focus {
  border-color: #7c3aed;
}

.form-input::placeholder {
  color: #444460;
}

.auth-error {
  padding: 0.625rem 0.875rem;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 8px;
  color: #f87171;
  font-size: 0.875rem;
}

.btn {
  padding: 0.625rem 1rem;
  border-radius: 8px;
  font-size: 0.9375rem;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 0.15s;
  text-align: center;
}

.btn--primary {
  background: #7c3aed;
  color: #fff;
}

.btn--primary:hover:not(:disabled) {
  background: #6d28d9;
}

.btn--primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn--full {
  width: 100%;
}

.auth-footer {
  margin-top: 1.25rem;
  text-align: center;
  font-size: 0.875rem;
  color: #6666a0;
}

.auth-link {
  color: #a78bfa;
  text-decoration: none;
  font-weight: 500;
}

.auth-link:hover {
  text-decoration: underline;
}
</style>
