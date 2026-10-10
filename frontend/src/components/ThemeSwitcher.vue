<script setup lang="ts">
import { useThemeStore } from '@/stores/theme'
import type { ThemeMode } from '@/types/theme'

defineProps<{
  compact?: boolean
}>()

const themeStore = useThemeStore()

const options: { mode: ThemeMode; label: string; title: string }[] = [
  { mode: 'light', label: 'Light', title: 'Light mode' },
  { mode: 'dark', label: 'Dark', title: 'Dark mode' },
  { mode: 'system', label: 'System', title: 'Follow system appearance' },
]

function selectMode(m: ThemeMode) {
  themeStore.setMode(m)
}
</script>

<template>
  <div class="theme-switcher" :class="{ 'theme-switcher--compact': compact }" role="radiogroup" aria-label="Theme mode selector">
    <button
      v-for="opt in options"
      :key="opt.mode"
      type="button"
      class="theme-btn"
      :class="{ 'theme-btn--active': themeStore.mode === opt.mode }"
      :title="opt.title"
      :aria-checked="themeStore.mode === opt.mode"
      role="radio"
      @click="selectMode(opt.mode)"
    >
      <!-- Sun Icon -->
      <svg
        v-if="opt.mode === 'light'"
        class="theme-icon"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <circle cx="12" cy="12" r="4" />
        <path d="M12 2v2" />
        <path d="M12 20v2" />
        <path d="m4.93 4.93 1.41 1.41" />
        <path d="m17.66 17.66 1.41 1.41" />
        <path d="M2 12h2" />
        <path d="M20 12h2" />
        <path d="m6.34 17.66-1.41 1.41" />
        <path d="m19.07 4.93-1.41 1.41" />
      </svg>

      <!-- Moon Icon -->
      <svg
        v-else-if="opt.mode === 'dark'"
        class="theme-icon"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z" />
      </svg>

      <!-- System / Monitor Icon -->
      <svg
        v-else
        class="theme-icon"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <rect width="20" height="14" x="2" y="3" rx="2" />
        <line x1="8" x2="16" y1="21" y2="21" />
        <line x1="12" x2="12" y1="17" y2="21" />
      </svg>

      <span v-if="!compact" class="theme-label">{{ opt.label }}</span>
    </button>
  </div>
</template>

<style scoped>
.theme-switcher {
  display: inline-flex;
  align-items: center;
  background: var(--bg-surface-elevated, #181820);
  border: 1px solid var(--border-subtle, #22222e);
  border-radius: 999px;
  padding: 3px;
  gap: 2px;
  transition: all var(--transition-fast, 0.15s ease);
}

.theme-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.375rem;
  padding: 0.35rem 0.75rem;
  border-radius: 999px;
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--text-muted, #9494a8);
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all var(--transition-fast, 0.15s ease);
  user-select: none;
}

.theme-switcher--compact .theme-btn {
  padding: 0.35rem;
  width: 28px;
  height: 28px;
}

.theme-icon {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}

.theme-label {
  line-height: 1;
}

.theme-btn:hover:not(.theme-btn--active) {
  color: var(--text-main, #f4f4f7);
  background: var(--bg-surface-hover, #21212c);
}

.theme-btn--active {
  color: var(--text-main, #f4f4f7);
  background: var(--primary, #7c3aed);
  box-shadow: var(--shadow-sm);
}

[data-theme="light"] .theme-btn--active {
  color: #ffffff;
}
</style>
