<script setup lang="ts">
defineProps<{
  show: boolean
  title?: string
  message: string
  confirmText?: string
  cancelText?: string
  variant?: 'danger' | 'primary' | 'warning'
  loading?: boolean
}>()

const emit = defineEmits<{
  (e: 'confirm'): void
  (e: 'cancel'): void
}>()
</script>

<template>
  <Teleport to="body">
    <Transition name="dialog-fade">
      <div v-if="show" class="dialog-backdrop" @click.self="emit('cancel')">
        <div class="dialog-box" role="dialog" aria-modal="true">
          <div class="dialog-header">
            <div class="dialog-icon" :class="`dialog-icon--${variant || 'danger'}`">
              <svg v-if="variant === 'danger'" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                <line x1="12" y1="9" x2="12" y2="13"/>
                <line x1="12" y1="17" x2="12.01" y2="17"/>
              </svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="16" x2="12" y2="12"/>
                <line x1="12" y1="8" x2="12.01" y2="8"/>
              </svg>
            </div>
            <h3 class="dialog-title">{{ title || 'Confirm Action' }}</h3>
          </div>

          <div class="dialog-body">
            <p class="dialog-message">{{ message }}</p>
          </div>

          <div class="dialog-footer">
            <button
              type="button"
              class="btn btn--ghost"
              :disabled="loading"
              @click="emit('cancel')"
            >
              {{ cancelText || 'Cancel' }}
            </button>
            <button
              type="button"
              class="btn"
              :class="variant === 'primary' ? 'btn--primary' : 'btn--danger'"
              :disabled="loading"
              @click="emit('confirm')"
            >
              {{ loading ? 'Processing...' : (confirmText || 'Confirm') }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.dialog-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  backdrop-filter: blur(2px);
}

.dialog-box {
  background: #18181c;
  border: 1px solid #2a2a35;
  border-radius: 12px;
  width: 100%;
  max-width: 440px;
  padding: 1.5rem;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 10px 10px -5px rgba(0, 0, 0, 0.2);
}

.dialog-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.875rem;
}

.dialog-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  flex-shrink: 0;
}

.dialog-icon--danger {
  background: rgba(239, 68, 68, 0.15);
  color: #f87171;
}

.dialog-icon--primary {
  background: rgba(124, 58, 237, 0.15);
  color: #a78bfa;
}

.dialog-icon--warning {
  background: rgba(245, 158, 11, 0.15);
  color: #fbbf24;
}

.dialog-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #f1f1f8;
  margin: 0;
}

.dialog-body {
  margin-bottom: 1.5rem;
}

.dialog-message {
  font-size: 0.9375rem;
  color: #9999b3;
  line-height: 1.5;
  margin: 0;
}

.dialog-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.75rem;
}

.btn {
  padding: 0.5rem 1.125rem;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 0.15s;
}

.btn--ghost {
  background: transparent;
  color: #9999b3;
  border: 1px solid #2a2a35;
}

.btn--ghost:hover:not(:disabled) {
  background: #2a2a35;
  color: #f1f1f8;
}

.btn--danger {
  background: #dc2626;
  color: #fff;
}

.btn--danger:hover:not(:disabled) {
  background: #b91c1c;
}

.btn--primary {
  background: #7c3aed;
  color: #fff;
}

.btn--primary:hover:not(:disabled) {
  background: #6d28d9;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Transitions */
.dialog-fade-enter-active,
.dialog-fade-leave-active {
  transition: opacity 0.2s ease;
}

.dialog-fade-enter-from,
.dialog-fade-leave-to {
  opacity: 0;
}

.dialog-fade-enter-active .dialog-box,
.dialog-fade-leave-active .dialog-box {
  transition: transform 0.2s ease;
}

.dialog-fade-enter-from .dialog-box,
.dialog-fade-leave-to .dialog-box {
  transform: scale(0.95);
}
</style>
