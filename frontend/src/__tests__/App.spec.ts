import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import AppLogo from '../components/AppLogo.vue'

describe('AppLogo', () => {
  it('renders SVG puzzle emblem properly', () => {
    const wrapper = mount(AppLogo, {
      props: {
        size: 32,
      },
    })
    expect(wrapper.find('svg').exists()).toBe(true)
    expect(wrapper.find('rect').exists()).toBe(true)
    expect(wrapper.find('path').exists()).toBe(true)
  })
})
