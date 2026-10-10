import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import ThemeSwitcher from '@/components/ThemeSwitcher.vue'
import PaletteSelector from '@/components/PaletteSelector.vue'
import SettingsView from '@/views/Settings/SettingsView.vue'
import { useThemeStore } from '@/stores/theme'

describe('ThemeSwitcher.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
  })

  it('renders all 3 mode options with correct accessible roles', () => {
    const wrapper = mount(ThemeSwitcher)
    const buttons = wrapper.findAll('button')
    expect(buttons.length).toBe(3)
    expect(wrapper.attributes('role')).toBe('radiogroup')
  })

  it('switches theme mode on button click', async () => {
    const wrapper = mount(ThemeSwitcher)
    const store = useThemeStore()

    const buttons = wrapper.findAll('button')
    // Click Light button
    await buttons[0]!.trigger('click')
    expect(store.mode).toBe('light')

    // Click Dark button
    await buttons[1]!.trigger('click')
    expect(store.mode).toBe('dark')

    // Click System button
    await buttons[2]!.trigger('click')
    expect(store.mode).toBe('system')
  })

  it('renders in compact mode without labels', () => {
    const wrapper = mount(ThemeSwitcher, {
      props: { compact: true },
    })
    expect(wrapper.classes()).toContain('theme-switcher--compact')
    expect(wrapper.find('.theme-label').exists()).toBe(false)
  })
})

describe('PaletteSelector.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
  })

  it('renders dark palettes when themeTarget is dark', async () => {
    const wrapper = mount(PaletteSelector, {
      props: { themeTarget: 'dark' },
    })
    const cards = wrapper.findAll('.palette-card')
    expect(cards.length).toBe(5)

    const store = useThemeStore()
    // Select second palette (emerald)
    await cards[1]!.trigger('click')
    expect(store.darkPalette).toBe('emerald')
  })

  it('renders light palettes when themeTarget is light', async () => {
    const wrapper = mount(PaletteSelector, {
      props: { themeTarget: 'light' },
    })
    const cards = wrapper.findAll('.palette-card')
    expect(cards.length).toBe(5)

    const store = useThemeStore()
    // Select second palette (frost)
    await cards[1]!.trigger('click')
    expect(store.lightPalette).toBe('frost')
  })
})

describe('SettingsView.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
  })

  it('renders appearance sections and live preview card', () => {
    const wrapper = mount(SettingsView)
    expect(wrapper.find('.settings-title').text()).toContain('Appearance & Preferences')
    expect(wrapper.findAll('.settings-section').length).toBe(4)
    expect(wrapper.find('.preview-card').exists()).toBe(true)
  })
})
