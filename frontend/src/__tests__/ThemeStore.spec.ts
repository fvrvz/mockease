import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useThemeStore, DARK_PALETTES, LIGHT_PALETTES } from '@/stores/theme'

describe('ThemeStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    document.documentElement.removeAttribute('data-theme')
    document.documentElement.removeAttribute('data-palette')
    vi.restoreAllMocks()
  })

  it('initializes with default system mode and palettes', () => {
    const store = useThemeStore()
    expect(store.mode).toBe('system')
    expect(store.darkPalette).toBe('violet')
    expect(store.lightPalette).toBe('iris')
    expect(DARK_PALETTES.length).toBe(5)
    expect(LIGHT_PALETTES.length).toBe(5)
  })

  it('correctly resolves theme when mode is dark or light', () => {
    const store = useThemeStore()

    store.setMode('dark')
    expect(store.mode).toBe('dark')
    expect(store.resolvedTheme).toBe('dark')
    expect(store.activePalette).toBe(store.darkPalette)
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
    expect(document.documentElement.getAttribute('data-palette')).toBe('violet')

    store.setMode('light')
    expect(store.mode).toBe('light')
    expect(store.resolvedTheme).toBe('light')
    expect(store.activePalette).toBe(store.lightPalette)
    expect(document.documentElement.getAttribute('data-theme')).toBe('light')
    expect(document.documentElement.getAttribute('data-palette')).toBe('iris')
  })

  it('updates dark palette and persists in localStorage', () => {
    const store = useThemeStore()
    store.setMode('dark')
    store.setDarkPalette('emerald')

    expect(store.darkPalette).toBe('emerald')
    expect(localStorage.getItem('mockease_dark_palette')).toBe('emerald')
    expect(document.documentElement.getAttribute('data-palette')).toBe('emerald')
  })

  it('updates light palette and persists in localStorage', () => {
    const store = useThemeStore()
    store.setMode('light')
    store.setLightPalette('frost')

    expect(store.lightPalette).toBe('frost')
    expect(localStorage.getItem('mockease_light_palette')).toBe('frost')
    expect(document.documentElement.getAttribute('data-palette')).toBe('frost')
  })

  it('handles system appearance listener and matches media', () => {
    let capturedCallback: ((e: MediaQueryListEvent) => void) | null = null

    const mockMatchMedia = vi.fn().mockImplementation((query: string) => {
      return {
        matches: true,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn((event: string, cb: (e: MediaQueryListEvent) => void) => {
          if (event === 'change') capturedCallback = cb
        }),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      }
    })

    window.matchMedia = mockMatchMedia as unknown as typeof window.matchMedia

    const store = useThemeStore()
    store.setMode('system')
    store.initSystemListener()

    expect(store.systemPrefersDark).toBe(true)
    expect(store.resolvedTheme).toBe('dark')

    // Simulate system switching to light mode
    expect(capturedCallback).toBeTypeOf('function')
    const handler = capturedCallback as unknown as (e: MediaQueryListEvent) => void
    handler({ matches: false } as MediaQueryListEvent)
    expect(store.systemPrefersDark).toBe(false)
    expect(store.resolvedTheme).toBe('light')
  })

  it('loads existing preference from localStorage on initialization', () => {
    localStorage.setItem('mockease_theme_mode', 'light')
    localStorage.setItem('mockease_dark_palette', 'sapphire')
    localStorage.setItem('mockease_light_palette', 'sage')

    setActivePinia(createPinia())
    const store = useThemeStore()

    expect(store.mode).toBe('light')
    expect(store.darkPalette).toBe('sapphire')
    expect(store.lightPalette).toBe('sage')
  })
})
