<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

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
          <span class="brand-icon">🧩</span>
          <span class="brand-name">MockEase</span>
        </RouterLink>
      </div>
      <div class="app-header__actions">
        <span class="user-name">{{ authStore.user?.username }}</span>
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
  background: #0f0f11;
  color: #e8e8f0;
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1.5rem;
  height: 56px;
  background: #18181c;
  border-bottom: 1px solid #2a2a35;
  position: sticky;
  top: 0;
  z-index: 100;
}

.brand-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
  color: inherit;
}

.brand-icon {
  font-size: 1.25rem;
}

.brand-name {
  font-size: 1.125rem;
  font-weight: 700;
  color: #a78bfa;
  letter-spacing: -0.02em;
}

.app-header__actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.user-name {
  font-size: 0.875rem;
  color: #9999b3;
}

.btn {
  padding: 0.375rem 0.875rem;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all 0.15s;
}

.btn--ghost {
  background: transparent;
  color: #9999b3;
  border: 1px solid #2a2a35;
}

.btn--ghost:hover {
  background: #2a2a35;
  color: #e8e8f0;
}

.app-main {
  flex: 1;
}
</style>
