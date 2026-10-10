export type ThemeMode = 'light' | 'dark' | 'system'

export type ResolvedTheme = 'light' | 'dark'

export type DarkPaletteId = 'violet' | 'emerald' | 'sapphire' | 'amber' | 'onyx'

export type LightPaletteId = 'iris' | 'frost' | 'sage' | 'rose' | 'sandstone'

export interface PalettePreset<T extends string = string> {
  id: T
  name: string
  description: string
  accentColor: string
  surfaceColor: string
  bgColor: string
  previewBorder: string
}
