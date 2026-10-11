import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import AppLayout from '@/layouts/AppLayout.vue'
import { useAuthStore } from '@/stores/auth'

const mockPush = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}))

describe('AppLayout', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    mockPush.mockClear()
    localStorage.clear()
  })

  it('renders the header with brand logo, brand name, and theme controls', () => {
    const authStore = useAuthStore()
    authStore.user = {
      id: 'user-1',
      username: 'alice',
      email: 'alice@example.com',
      is_active: true,
    }

    const wrapper = mount(AppLayout, {
      global: {
        stubs: {
          RouterLink: {
            template: '<a :href="to"><slot /></a>',
            props: ['to'],
          },
          RouterView: true,
        },
      },
    })

    const brandName = wrapper.find('.brand-name')
    expect(brandName.exists()).toBe(true)
    expect(brandName.text()).toBe('MockEase')

    const brandLogo = wrapper.findComponent({ name: 'AppLogo' })
    expect(brandLogo.exists()).toBe(true)

    const themeSwitcher = wrapper.findComponent({ name: 'ThemeSwitcher' })
    expect(themeSwitcher.exists()).toBe(true)

    expect(wrapper.find('.user-name').text()).toBe('alice')
    expect(wrapper.find('.user-avatar').text()).toBe('A')
  })

  it('logs out and redirects to login on logout button click', async () => {
    const authStore = useAuthStore()
    authStore.user = {
      id: 'user-1',
      username: 'alice',
      email: 'alice@example.com',
      is_active: true,
    }
    const logoutSpy = vi.spyOn(authStore, 'logout')

    const wrapper = mount(AppLayout, {
      global: {
        stubs: {
          RouterLink: true,
          RouterView: true,
        },
      },
    })

    const logoutBtn = wrapper.find('button.btn--ghost')
    expect(logoutBtn.exists()).toBe(true)
    await logoutBtn.trigger('click')

    expect(logoutSpy).toHaveBeenCalled()
    expect(mockPush).toHaveBeenCalledWith({ name: 'login' })
  })
})
