import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import { authService } from '@/services/auth'

vi.mock('@/services/auth', () => ({
  authService: {
    login: vi.fn(),
    register: vi.fn(),
    me: vi.fn(),
  },
}))

describe('Auth Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    vi.clearAllMocks()
  })

  it('initializes with default unauthenticated state', () => {
    const store = useAuthStore()
    expect(store.isAuthenticated).toBe(false)
    expect(store.user).toBeNull()
    expect(store.token).toBeNull()
  })

  it('logs in successfully and sets token in state and localStorage', async () => {
    vi.mocked(authService.login).mockResolvedValueOnce({
      access_token: 'fake-jwt-token',
      token_type: 'bearer',
    })
    vi.mocked(authService.me).mockResolvedValueOnce({
      id: 'user-1',
      email: 'user@mockease.dev',
      username: 'mockuser',
      is_active: true,
    })

    const store = useAuthStore()
    await store.login('user@mockease.dev', 'password123')

    expect(store.isAuthenticated).toBe(true)
    expect(store.token).toBe('fake-jwt-token')
    expect(store.user?.username).toBe('mockuser')
    expect(localStorage.getItem('access_token')).toBe('fake-jwt-token')
  })

  it('registers successfully', async () => {
    vi.mocked(authService.register).mockResolvedValueOnce({
      id: 'user-2',
      email: 'reg@mockease.dev',
      username: 'reguser',
      is_active: true,
    })

    const store = useAuthStore()
    await store.register('reg@mockease.dev', 'reguser', 'password123')

    expect(authService.register).toHaveBeenCalledWith({
      email: 'reg@mockease.dev',
      username: 'reguser',
      password: 'password123',
    })
  })

  it('logs out and clears token from state and localStorage', () => {
    localStorage.setItem('access_token', 'token-to-clear')
    const store = useAuthStore()
    store.token = 'token-to-clear'
    store.user = { id: 'u1', email: 'e', username: 'u', is_active: true }

    store.logout()

    expect(store.token).toBeNull()
    expect(store.user).toBeNull()
    expect(store.isAuthenticated).toBe(false)
    expect(localStorage.getItem('access_token')).toBeNull()
  })
})
