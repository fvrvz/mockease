<script setup lang="ts">
import { computed } from 'vue'
import { useThemeStore, DARK_PALETTES, LIGHT_PALETTES } from '@/stores/theme'
import type { DarkPaletteId, LightPaletteId, PalettePreset } from '@/types/theme'

const props = defineProps<{
  themeTarget: 'dark' | 'light'
}>()

const themeStore = useThemeStore()

const palettes = computed<PalettePreset[]>(() => {
  return props.themeTarget === 'dark' ? DARK_PALETTES : LIGHT_PALETTES
})

const activeId = computed<string>(() => {
  return props.themeTarget === 'dark' ? themeStore.darkPalette : themeStore.lightPalette
})

function selectPalette(id: string) {
  if (props.themeTarget === 'dark') {
    themeStore.setDarkPalette(id as DarkPaletteId)
  } else {
    themeStore.setLightPalette(id as LightPaletteId)
  }
}
</script>

<template>
  <div class="palette-grid" role="radiogroup" :aria-label="`${themeTarget} color palette presets`">
    <button
      v-for="p in palettes"
      :key="p.id"
      type="button"
      class="palette-card"
      :class="{ 'palette-card--active': activeId === p.id }"
      :aria-checked="activeId === p.id"
      role="radio"
      @click="selectPalette(p.id)"
    >
      <div class="palette-card__header">
        <div class="swatches-preview">
          <!-- Background swatch -->
          <span
            class="swatch swatch--bg"
            :style="{ backgroundColor: p.bgColor, borderColor: p.previewBorder }"
            title="App Background"
          />
          <!-- Surface swatch -->
          <span
            class="swatch swatch--surface"
            :style="{ backgroundColor: p.surfaceColor, borderColor: p.previewBorder }"
            title="Surface Card"
          />
          <!-- Accent swatch -->
          <span
            class="swatch swatch--accent"
            :style="{ backgroundColor: p.accentColor }"
            title="Primary Accent"
          />
        </div>

        <div v-if="activeId === p.id" class="check-badge">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="20 6 9 17 4 12" />
          </svg>
        </div>
      </div>

      <div class="palette-card__body">
        <div class="palette-name">{{ p.name }}</div>
        <div class="palette-desc">{{ p.description }}</div>
      </div>
    </button>
  </div>
</template>

<style scoped>
.palette-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 1rem;
}

.palette-card {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  background: var(--bg-surface, #121217);
  border: 1px solid var(--border-subtle, #22222e);
  border-radius: 12px;
  padding: 1rem;
  cursor: pointer;
  text-align: left;
  transition: all var(--transition-fast, 0.15s ease);
  position: relative;
}

.palette-card:hover:not(.palette-card--active) {
  background: var(--bg-surface-elevated, #181820);
  border-color: var(--border-strong, #323242);
  transform: translateY(-2px);
}

.palette-card--active {
  border-color: var(--primary, #7c3aed);
  background: var(--bg-surface-elevated, #181820);
  box-shadow: 0 0 0 1px var(--primary, #7c3aed), var(--shadow-sm);
}

.palette-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.swatches-preview {
  display: flex;
  align-items: center;
  gap: -4px;
}

.swatch {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: 1px solid transparent;
  display: inline-block;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.swatch--bg {
  z-index: 1;
}

.swatch--surface {
  margin-left: -6px;
  z-index: 2;
}

.swatch--accent {
  margin-left: -6px;
  z-index: 3;
}

.check-badge {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--primary, #7c3aed);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 3px;
}

.check-badge svg {
  width: 100%;
  height: 100%;
}

.palette-card__body {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.palette-name {
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--text-main, #f4f4f7);
}

.palette-desc {
  font-size: 0.75rem;
  color: var(--text-muted, #9494a8);
  line-height: 1.35;
}
</style>
