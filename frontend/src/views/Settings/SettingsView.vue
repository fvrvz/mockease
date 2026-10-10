<script setup lang="ts">
import { useThemeStore } from '@/stores/theme'
import ThemeSwitcher from '@/components/ThemeSwitcher.vue'
import PaletteSelector from '@/components/PaletteSelector.vue'

const themeStore = useThemeStore()
</script>

<template>
  <div class="settings-page">
    <header class="settings-header">
      <div>
        <h1 class="settings-title">Appearance & Preferences</h1>
        <p class="settings-subtitle">Customize your visual interface, theme mode, and curated color palettes.</p>
      </div>
    </header>

    <div class="settings-content">
      <!-- 1. Theme Mode -->
      <section class="settings-section">
        <div class="section-heading">
          <div>
            <h2 class="section-title">Theme Mode</h2>
            <p class="section-desc">Choose between Light, Dark, or automatically match your system appearance.</p>
          </div>
          <div class="status-pill">
            <span class="status-dot"></span>
            Active: {{ themeStore.resolvedTheme === 'dark' ? 'Dark Mode' : 'Light Mode' }}
          </div>
        </div>

        <div class="theme-mode-row">
          <ThemeSwitcher />
        </div>
      </section>

      <!-- 2. Dark Theme Color Palettes -->
      <section class="settings-section">
        <div class="section-heading">
          <div>
            <h2 class="section-title">Dark Theme Palettes</h2>
            <p class="section-desc">Predefined curated color presets applied when dark mode is active.</p>
          </div>
        </div>

        <PaletteSelector theme-target="dark" />
      </section>

      <!-- 3. Light Theme Color Palettes -->
      <section class="settings-section">
        <div class="section-heading">
          <div>
            <h2 class="section-title">Light Theme Palettes</h2>
            <p class="section-desc">Predefined curated color presets applied when light mode is active.</p>
          </div>
        </div>

        <PaletteSelector theme-target="light" />
      </section>

      <!-- 4. Realtime Preview -->
      <section class="settings-section">
        <div class="section-heading">
          <div>
            <h2 class="section-title">Live Preview</h2>
            <p class="section-desc">Preview how your active color palette styles core components.</p>
          </div>
        </div>

        <div class="preview-card">
          <div class="preview-card__header">
            <div class="preview-badge">Active Palette: {{ themeStore.activePalette }}</div>
            <span class="preview-tag">HTTP 200 OK</span>
          </div>

          <div class="preview-card__content">
            <div class="preview-inputs">
              <label class="preview-label">Sample Endpoint Path</label>
              <input type="text" class="preview-input" value="/api/v1/users" readonly />
            </div>

            <div class="preview-actions">
              <button type="button" class="btn btn--primary">Primary Button</button>
              <button type="button" class="btn btn--ghost">Secondary Action</button>
              <span class="badge badge--success">Ready</span>
              <span class="badge badge--warning">Mocking</span>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.settings-page {
  max-width: 960px;
  margin: 0 auto;
  padding: 2.5rem 1.75rem 4rem;
}

.settings-header {
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid var(--border-subtle, #22222e);
}

.settings-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--text-main, #f4f4f7);
  letter-spacing: -0.02em;
  margin: 0 0 0.35rem;
}

.settings-subtitle {
  font-size: 0.9375rem;
  color: var(--text-muted, #9494a8);
  margin: 0;
}

.settings-content {
  display: flex;
  flex-direction: column;
  gap: 2.5rem;
}

.settings-section {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.section-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.section-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-main, #f4f4f7);
  margin: 0 0 0.25rem;
}

.section-desc {
  font-size: 0.875rem;
  color: var(--text-muted, #9494a8);
  margin: 0;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.35rem 0.85rem;
  background: var(--bg-surface-elevated, #181820);
  border: 1px solid var(--border-subtle, #22222e);
  border-radius: 999px;
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--text-main, #f4f4f7);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--primary, #7c3aed);
}

.theme-mode-row {
  display: flex;
  align-items: center;
}

.preview-card {
  background: var(--bg-surface, #121217);
  border: 1px solid var(--border-subtle, #22222e);
  border-radius: 14px;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  box-shadow: var(--shadow-sm);
}

.preview-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.preview-badge {
  font-size: 0.8125rem;
  font-weight: 600;
  text-transform: capitalize;
  color: var(--primary, #7c3aed);
}

.preview-tag {
  font-family: monospace;
  font-size: 0.75rem;
  padding: 0.2rem 0.5rem;
  background: var(--success-bg, rgba(16, 185, 129, 0.12));
  color: var(--success, #10b981);
  border-radius: 6px;
}

.preview-card__content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.preview-inputs {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.preview-label {
  font-size: 0.8125rem;
  color: var(--text-muted, #9494a8);
}

.preview-input {
  padding: 0.625rem 0.875rem;
  background: var(--bg-surface-elevated, #181820);
  border: 1px solid var(--border-subtle, #22222e);
  border-radius: 8px;
  color: var(--text-main, #f4f4f7);
  font-size: 0.9375rem;
  outline: none;
}

.preview-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.btn {
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all var(--transition-fast, 0.15s ease);
}

.btn--primary {
  background: var(--primary, #7c3aed);
  color: #ffffff;
}

.btn--primary:hover {
  background: var(--primary-hover, #6d28d9);
}

.btn--ghost {
  background: transparent;
  color: var(--text-muted, #9494a8);
  border: 1px solid var(--border-subtle, #22222e);
}

.btn--ghost:hover {
  background: var(--bg-surface-hover, #21212c);
  color: var(--text-main, #f4f4f7);
}

.badge {
  padding: 0.25rem 0.65rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
}

.badge--success {
  background: var(--success-bg, rgba(16, 185, 129, 0.12));
  color: var(--success, #10b981);
}

.badge--warning {
  background: var(--warning-bg, rgba(245, 158, 11, 0.12));
  color: var(--warning, #f59e0b);
}
</style>
