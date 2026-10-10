import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import type {
  ThemeMode,
  ResolvedTheme,
  DarkPaletteId,
  LightPaletteId,
  PalettePreset,
} from '@/types/theme'

export const DARK_PALETTES: PalettePreset<DarkPaletteId>[] = [
  {
    id: 'violet',
    name: 'Midnight Violet',
    description: 'Deep obsidian slate with electric violet accents',
    accentColor: '#7c3aed',
    surfaceColor: '#121217',
    bgColor: '#09090b',
    previewBorder: '#272733',
  },
  {
    id: 'emerald',
    name: 'Cyber Emerald',
    description: 'Tech-focused dark charcoal with vibrant emerald neon',
    accentColor: '#10b981',
    surfaceColor: '#0f1814',
    bgColor: '#080f0c',
    previewBorder: '#163325',
  },
  {
    id: 'sapphire',
    name: 'Ocean Sapphire',
    description: 'Deep navy night with crisp oceanic sapphire glow',
    accentColor: '#3b82f6',
    surfaceColor: '#0f172a',
    bgColor: '#070d18',
    previewBorder: '#1e293b',
  },
  {
    id: 'amber',
    name: 'Sunset Amber',
    description: 'Warm dark espresso with rich amber and copper tones',
    accentColor: '#f59e0b',
    surfaceColor: '#1c140d',
    bgColor: '#140d08',
    previewBorder: '#382618',
  },
  {
    id: 'onyx',
    name: 'Pure Onyx',
    description: 'True pitch black OLED with crisp minimalist monochrome',
    accentColor: '#e4e4e7',
    surfaceColor: '#111111',
    bgColor: '#000000',
    previewBorder: '#27272a',
  },
]

export const LIGHT_PALETTES: PalettePreset<LightPaletteId>[] = [
  {
    id: 'iris',
    name: 'Clean Iris',
    description: 'Crisp bright white canvas with modern royal iris indigo',
    accentColor: '#6366f1',
    surfaceColor: '#ffffff',
    bgColor: '#f8fafc',
    previewBorder: '#e2e8f0',
  },
  {
    id: 'frost',
    name: 'Nordic Frost',
    description: 'Cool glacial slate paired with energetic cyan and blue',
    accentColor: '#0284c7',
    surfaceColor: '#ffffff',
    bgColor: '#f1f5f9',
    previewBorder: '#cbd5e1',
  },
  {
    id: 'sage',
    name: 'Sage Mist',
    description: 'Gentle organic mist with calming botanical green accents',
    accentColor: '#059669',
    surfaceColor: '#ffffff',
    bgColor: '#f4f7f4',
    previewBorder: '#d1fae5',
  },
  {
    id: 'rose',
    name: 'Rose Pearl',
    description: 'Subtle warm pearl foundation with bold rose accents',
    accentColor: '#e11d48',
    surfaceColor: '#ffffff',
    bgColor: '#faf5f5',
    previewBorder: '#ffe4e6',
  },
  {
    id: 'sandstone',
    name: 'Warm Sandstone',
    description: 'Earthy cream paper with golden amber and terracotta',
    accentColor: '#d97706',
    surfaceColor: '#ffffff',
    bgColor: '#fafaf9',
    previewBorder: '#e7e5e4',
  },
]

const STORAGE_KEYS = {
  MODE: 'mockease_theme_mode',
  DARK_PALETTE: 'mockease_dark_palette',
  LIGHT_PALETTE: 'mockease_light_palette',
} as const

export const useThemeStore = defineStore('theme', () => {
  const storedMode = (typeof localStorage !== 'undefined'
    ? localStorage.getItem(STORAGE_KEYS.MODE)
    : null) as ThemeMode | null
  const mode = ref<ThemeMode>(
    storedMode === 'light' || storedMode === 'dark' || storedMode === 'system'
      ? storedMode
      : 'system',
  )

  const storedDarkPalette = (typeof localStorage !== 'undefined'
    ? localStorage.getItem(STORAGE_KEYS.DARK_PALETTE)
    : null) as DarkPaletteId | null
  const darkPalette = ref<DarkPaletteId>(
    DARK_PALETTES.some((p) => p.id === storedDarkPalette)
      ? (storedDarkPalette as DarkPaletteId)
      : 'violet',
  )

  const storedLightPalette = (typeof localStorage !== 'undefined'
    ? localStorage.getItem(STORAGE_KEYS.LIGHT_PALETTE)
    : null) as LightPaletteId | null
  const lightPalette = ref<LightPaletteId>(
    LIGHT_PALETTES.some((p) => p.id === storedLightPalette)
      ? (storedLightPalette as LightPaletteId)
      : 'iris',
  )

  const systemPrefersDark = ref(
    typeof window !== 'undefined' &&
      window.matchMedia &&
      window.matchMedia('(prefers-color-scheme: dark)').matches,
  )

  const resolvedTheme = computed<ResolvedTheme>(() => {
    if (mode.value === 'system') {
      return systemPrefersDark.value ? 'dark' : 'light'
    }
    return mode.value
  })

  const activePalette = computed<string>(() => {
    return resolvedTheme.value === 'dark' ? darkPalette.value : lightPalette.value
  })

  function applyThemeToDom() {
    if (typeof document === 'undefined') return
    const root = document.documentElement
    root.setAttribute('data-theme', resolvedTheme.value)
    root.setAttribute('data-palette', activePalette.value)
  }

  function setMode(newMode: ThemeMode) {
    mode.value = newMode
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(STORAGE_KEYS.MODE, newMode)
    }
    applyThemeToDom()
  }

  function setDarkPalette(paletteId: DarkPaletteId) {
    darkPalette.value = paletteId
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(STORAGE_KEYS.DARK_PALETTE, paletteId)
    }
    applyThemeToDom()
  }

  function setLightPalette(paletteId: LightPaletteId) {
    lightPalette.value = paletteId
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(STORAGE_KEYS.LIGHT_PALETTE, paletteId)
    }
    applyThemeToDom()
  }

  function initSystemListener() {
    if (typeof window === 'undefined' || !window.matchMedia) return
    const media = window.matchMedia('(prefers-color-scheme: dark)')
    systemPrefersDark.value = media.matches

    const handler = (e: MediaQueryListEvent) => {
      systemPrefersDark.value = e.matches
      if (mode.value === 'system') {
        applyThemeToDom()
      }
    }

    if (media.addEventListener) {
      media.addEventListener('change', handler)
    } else if (media.addListener) {
      media.addListener(handler)
    }
  }

  return {
    mode,
    darkPalette,
    lightPalette,
    systemPrefersDark,
    resolvedTheme,
    activePalette,
    setMode,
    setDarkPalette,
    setLightPalette,
    applyThemeToDom,
    initSystemListener,
  }
})
