import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import type { User } from '@/types/auth'
import { authService } from '@/services/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('access_token'))
  const loading = ref(false)

  const isAuthenticated = computed(() => !!token.value)

  async function login(email: string, password: string) {
    loading.value = true
    try {
      const res = await authService.login({ email, password })
      token.value = res.access_token
      localStorage.setItem('access_token', res.access_token)
      await fetchMe()
    } finally {
      loading.value = false
    }
  }

  async function register(email: string, username: string, password: string) {
    loading.value = true
    try {
      await authService.register({ email, username, password })
    } finally {
      loading.value = false
    }
  }

  async function fetchMe() {
    try {
      user.value = await authService.me()
    } catch {
      logout()
    }
  }

  function logout() {
    user.value = null
    token.value = null
    localStorage.removeItem('access_token')
  }

  // Initialize on store creation
  if (token.value) {
    fetchMe()
  }

  return { user, token, loading, isAuthenticated, login, register, fetchMe, logout }
})
