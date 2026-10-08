import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import NotFound from '@/views/NotFound.vue'

describe('NotFound View', () => {
  it('renders 404 header and description', () => {
    const wrapper = mount(NotFound, {
      global: {
        stubs: ['RouterLink'],
      },
    })
    expect(wrapper.text()).toContain('404')
    expect(wrapper.text()).toContain('Page not found')
    expect(wrapper.text()).toContain("The page you're looking for doesn't exist.")
  })
})
