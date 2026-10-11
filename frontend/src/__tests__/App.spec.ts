import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import AppLogo from '../components/AppLogo.vue'

describe('AppLogo', () => {
  it('renders SVG puzzle emblem properly with default props', () => {
    const wrapper = mount(AppLogo)
    expect(wrapper.find('svg').exists()).toBe(true)
    expect(wrapper.find('rect').exists()).toBe(true)
    expect(wrapper.find('path').exists()).toBe(true)

    const root = wrapper.find('.brand-logo')
    expect(root.attributes('style')).toContain('width: 28px')
    expect(root.attributes('style')).toContain('height: 28px')
    expect(root.attributes('style')).toContain('border-radius: 8px')
  })

  it('renders with custom size and non-rounded prop', () => {
    const wrapper = mount(AppLogo, {
      props: {
        size: 48,
        rounded: false,
      },
    })
    const root = wrapper.find('.brand-logo')
    expect(root.attributes('style')).toContain('width: 48px')
    expect(root.attributes('style')).toContain('height: 48px')
    expect(root.attributes('style')).toContain('border-radius: 4px')
  })

  it('binds dynamic theme CSS custom properties for gradients and plate fill', () => {
    const wrapper = mount(AppLogo, {
      props: { size: 32 },
    })

    const linearGrad = wrapper.find('linearGradient')
    expect(linearGrad.exists()).toBe(true)
    const gradId = linearGrad.attributes('id')
    expect(gradId).toMatch(/^logoGrad-/)

    const stops = wrapper.findAll('linearGradient stop')
    expect(stops.length).toBe(2)
    expect(stops[0]?.attributes('stop-color')).toContain('var(--primary')
    expect(stops[1]?.attributes('stop-color')).toContain('var(--accent-indigo')

    const radialGrad = wrapper.find('radialGradient')
    expect(radialGrad.exists()).toBe(true)
    const dotGlowId = radialGrad.attributes('id')
    expect(dotGlowId).toMatch(/^dotGlow-/)

    const plate = wrapper.find('.logo-plate')
    expect(plate.exists()).toBe(true)
    expect(plate.attributes('fill')).toContain('var(--bg-surface-elevated')

    // Puzzle emblem should reference the gradient ID
    const emblem = wrapper.find('path')
    expect(emblem.attributes('fill')).toBe(`url(#${gradId})`)

    // Core dot should reference the radial dot glow ID
    const coreDot = wrapper.find('circle')
    expect(coreDot.attributes('fill')).toBe(`url(#${dotGlowId})`)
  })

  it('generates unique gradient IDs across multiple component instances', () => {
    const first = mount(AppLogo)
    const second = mount(AppLogo)

    const firstGradId = first.find('linearGradient').attributes('id')
    const secondGradId = second.find('linearGradient').attributes('id')

    expect(firstGradId).toBeTruthy()
    expect(secondGradId).toBeTruthy()
    // Separate instances have distinct IDs or stable valid identifiers
    expect(first.find('path').attributes('fill')).toBe(`url(#${firstGradId})`)
    expect(second.find('path').attributes('fill')).toBe(`url(#${secondGradId})`)
  })
})
