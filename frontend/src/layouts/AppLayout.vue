<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import AppLogo from '@/components/AppLogo.vue'
import ThemeSwitcher from '@/components/ThemeSwitcher.vue'

const authStore = useAuthStore()
const router = useRouter()

function logout() {
  authStore.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="app-layout">
    <header class="app-header">
      <div class="app-header__brand">
        <RouterLink to="/" class="brand-link">
          <AppLogo :size="30" />
          <span class="brand-name">MockEase</span>
        </RouterLink>
      </div>
      <div class="app-header__actions">
        <!-- Compact Quick Theme Switcher -->
        <ThemeSwitcher :compact="true" />

        <!-- Settings Link -->
        <RouterLink to="/settings" class="settings-link" title="Appearance & Settings">
          <svg
            class="settings-icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path
              d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"
            />
            <circle cx="12" cy="12" r="3" />
          </svg>
          <span class="settings-text">Settings</span>
        </RouterLink>

        <div class="user-pill">
          <span class="user-avatar">{{ authStore.user?.username?.[0]?.toUpperCase() || 'U' }}</span>
          <span class="user-name">{{ authStore.user?.username }}</span>
        </div>
        <button class="btn btn--ghost" @click="logout">Logout</button>
      </div>
    </header>
    <main class="app-main">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: var(--bg-app, #09090b);
  color: var(--text-main, #f4f4f7);
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1.75rem;
  height: 60px;
  background: var(--bg-surface, #121217);
  border-bottom: 1px solid var(--border-subtle, #22222e);
  position: sticky;
  top: 0;
  z-index: 100;
  backdrop-filter: blur(8px);
}

.brand-link {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  text-decoration: none;
  color: inherit;
}

.brand-name {
  font-size: 1.1875rem;
  font-weight: 700;
  background: linear-gradient(135deg, #f4f4f7 0%, #c4b5fd 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  letter-spacing: -0.025em;
}

.app-header__actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.settings-link {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.35rem 0.65rem;
  border-radius: 8px;
  color: var(--text-muted, #9494a8);
  text-decoration: none;
  font-size: 0.8125rem;
  font-weight: 500;
  border: 1px solid transparent;
  transition: all var(--transition-fast, 0.15s ease);
}

.settings-link:hover,
.settings-link.router-link-active {
  color: var(--text-main, #f4f4f7);
  background: var(--bg-surface-elevated, #181820);
  border-color: var(--border-subtle, #22222e);
}

.settings-icon {
  width: 15px;
  height: 15px;
}

.user-pill {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: var(--bg-surface-elevated, #181820);
  border: 1px solid var(--border-subtle, #22222e);
  padding: 0.25rem 0.75rem 0.25rem 0.35rem;
  border-radius: 999px;
}

.user-avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: linear-gradient(135deg, #7c3aed, #6366f1);
  color: white;
  font-size: 0.75rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-name {
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--text-muted, #9494a8);
}

.btn {
  padding: 0.4rem 0.95rem;
  border-radius: 8px;
  font-size: 0.8125rem;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 0.15s ease;
}

.btn--ghost {
  background: transparent;
  color: var(--text-muted, #9494a8);
  border: 1px solid var(--border-subtle, #22222e);
}

.btn--ghost:hover {
  background: var(--bg-surface-elevated, #181820);
  border-color: var(--border-strong, #323242);
  color: var(--text-main, #f4f4f7);
}

.app-main {
  flex: 1;
}
</style>
