import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import LoginView from '@/views/auth/LoginView.vue'
import RegisterView from '@/views/auth/RegisterView.vue'
import { useAuthStore } from '@/stores/auth'

const mockPush = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}))

describe('Auth Views', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    mockPush.mockClear()
    localStorage.clear()
  })

  describe('LoginView', () => {
    it('renders login form and submits credentials', async () => {
      const authStore = useAuthStore()
      authStore.login = vi.fn().mockResolvedValueOnce(undefined)

      const wrapper = mount(LoginView, {
        global: {
          stubs: ['RouterLink'],
        },
      })

      expect(wrapper.text()).toContain('MockEase')
      expect(wrapper.text()).toContain('Sign in to your account')

      const emailInput = wrapper.find('input[type="email"]')
      const passwordInput = wrapper.find('input[type="password"]')
      await emailInput.setValue('test@mockease.dev')
      await passwordInput.setValue('password123')

      await wrapper.find('form').trigger('submit.prevent')
      expect(authStore.login).toHaveBeenCalledWith('test@mockease.dev', 'password123')
      expect(mockPush).toHaveBeenCalledWith({ name: 'dashboard' })
    })

    it('toggles password visibility when eye icon button is clicked', async () => {
      const wrapper = mount(LoginView, {
        global: {
          stubs: ['RouterLink'],
        },
      })
      const passwordInput = wrapper.find('input[type="password"]')
      expect(passwordInput.exists()).toBe(true)

      const toggleBtn = wrapper.find('.password-toggle-btn')
      await toggleBtn.trigger('click')

      expect(wrapper.find('input[type="text"]').exists()).toBe(true)
    })
  })

  describe('RegisterView', () => {
    it('shows error if password and confirm password do not match', async () => {
      const wrapper = mount(RegisterView, {
        global: {
          stubs: ['RouterLink'],
        },
      })

      const emailInput = wrapper.find('input[type="email"]')
      const usernameInput = wrapper.find('input[type="text"]')
      const passwordInputs = wrapper.findAll('input[type="password"]')

      await emailInput.setValue('reg@mockease.dev')
      await usernameInput.setValue('reguser')
      await passwordInputs[0]!.setValue('password123')
      await passwordInputs[1]!.setValue('different123')

      await wrapper.find('form').trigger('submit.prevent')
      expect(wrapper.text()).toContain('Passwords do not match')
    })

    it('registers and redirects on matching passwords', async () => {
      const authStore = useAuthStore()
      authStore.register = vi.fn().mockResolvedValueOnce(undefined)
      authStore.login = vi.fn().mockResolvedValueOnce(undefined)

      const wrapper = mount(RegisterView, {
        global: {
          stubs: ['RouterLink'],
        },
      })

      const emailInput = wrapper.find('input[type="email"]')
      const usernameInput = wrapper.find('input[type="text"]')
      const passwordInputs = wrapper.findAll('input[type="password"]')

      await emailInput.setValue('reg@mockease.dev')
      await usernameInput.setValue('reguser')
      await passwordInputs[0]!.setValue('matching123')
      await passwordInputs[1]!.setValue('matching123')

      await wrapper.find('form').trigger('submit.prevent')
      expect(authStore.register).toHaveBeenCalledWith('reg@mockease.dev', 'reguser', 'matching123')
      expect(authStore.login).toHaveBeenCalledWith('reg@mockease.dev', 'matching123')
      expect(mockPush).toHaveBeenCalledWith({ name: 'dashboard' })
    })
  })
})
