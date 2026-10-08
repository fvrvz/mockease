<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useApplicationStore } from '@/stores/applications'

const router = useRouter()
const appStore = useApplicationStore()

const searchQuery = ref('')
const showCreateModal = ref(false)
const newAppName = ref('')
const newAppDesc = ref('')
const isCreating = ref(false)
const createError = ref<string | null>(null)

onMounted(() => {
  appStore.fetchApplications()
})

const filteredApps = computed(() => {
  if (!searchQuery.value.trim()) return appStore.applications
  const q = searchQuery.value.toLowerCase()
  return appStore.applications.filter(
    (a) => a.name.toLowerCase().includes(q) || (a.description && a.description.toLowerCase().includes(q))
  )
})

function closeCreateModal() {
  showCreateModal.value = false
  newAppName.value = ''
  newAppDesc.value = ''
  createError.value = null
}

async function handleCreate() {
  if (!newAppName.value.trim()) return
  isCreating.value = true
  createError.value = null
  try {
    const created = await appStore.createApplication({
      name: newAppName.value.trim(),
      description: newAppDesc.value.trim() || undefined,
    })
    closeCreateModal()
    router.push({ name: 'application', params: { id: created.id } })
  } catch (err: any) {
    createError.value = err?.response?.data?.detail ?? 'Failed to create application'
  } finally {
    isCreating.value = false
  }
}

async function handleToggle(id: string, e: Event) {
  e.stopPropagation()
  await appStore.toggleApplication(id)
}

async function handleDelete(id: string, name: string, e: Event) {
  e.stopPropagation()
  if (confirm(`Are you sure you want to delete "${name}"? This cannot be undone.`)) {
    await appStore.deleteApplication(id)
  }
}
</script>

<template>
  <div class="dashboard">
    <!-- Header -->
    <div class="dashboard__header">
      <div>
        <h1 class="dashboard__title">Applications</h1>
        <p class="dashboard__subtitle">Manage your mock API workspaces and endpoints</p>
      </div>
      <button class="btn btn--primary" @click="showCreateModal = true">
        + Create Application
      </button>
    </div>

    <!-- Search Bar -->
    <div v-if="appStore.applications.length > 0" class="dashboard__search">
      <input
        v-model="searchQuery"
        type="text"
        class="search-input"
        placeholder="Search applications..."
      />
    </div>

    <!-- Loading State -->
    <div v-if="appStore.loading && appStore.applications.length === 0" class="loading-state">
      Loading applications...
    </div>

    <!-- Empty State -->
    <div v-else-if="appStore.applications.length === 0" class="dashboard__empty">
      <span class="empty-icon">🧩</span>
      <h2 class="empty-title">No applications yet</h2>
      <p class="empty-desc">Create your first application to start designing and consuming mock APIs.</p>
      <button class="btn btn--primary" @click="showCreateModal = true">
        Create Application
      </button>
    </div>

    <!-- Applications Grid / List -->
    <div v-else class="apps-grid">
      <div
        v-for="app in filteredApps"
        :key="app.id"
        class="app-card"
        @click="router.push({ name: 'application', params: { id: app.id } })"
      >
        <div class="app-card__header">
          <div class="app-card__info">
            <h3 class="app-card__name">{{ app.name }}</h3>
            <span class="app-card__slug">/mock/{{ app.slug }}</span>
          </div>
          <div class="app-card__status">
            <span
              class="badge"
              :class="app.is_enabled ? 'badge--success' : 'badge--disabled'"
            >
              {{ app.is_enabled ? 'Enabled' : 'Disabled' }}
            </span>
          </div>
        </div>

        <p v-if="app.description" class="app-card__desc">{{ app.description }}</p>

        <div class="app-card__stats">
          <span>{{ app.controller_count ?? 0 }} Controllers</span>
          <span>•</span>
          <span>{{ app.endpoint_count ?? 0 }} APIs</span>
          <span v-if="(app.enabled_endpoint_count ?? 0) > 0" class="stats--enabled">
            ({{ app.enabled_endpoint_count }} enabled)
          </span>
        </div>

        <div class="app-card__actions" @click.stop>
          <button
            class="btn btn--sm btn--outline"
            @click="handleToggle(app.id, $event)"
          >
            {{ app.is_enabled ? 'Disable' : 'Enable' }}
          </button>
          <button
            class="btn btn--sm btn--primary"
            @click="router.push({ name: 'application', params: { id: app.id } })"
          >
            Open
          </button>
          <button
            class="btn btn--sm btn--danger-outline"
            @click="handleDelete(app.id, app.name, $event)"
          >
            Delete
          </button>
        </div>
      </div>
    </div>

    <!-- Create Application Modal -->
    <div v-if="showCreateModal" class="modal-backdrop" @click.self="closeCreateModal">
      <div class="modal">
        <h2 class="modal__title">Create Application</h2>
        <form @submit.prevent="handleCreate">
          <div class="form-group">
            <label class="form-label">Application Name</label>
            <input
              v-model="newAppName"
              type="text"
              class="form-input"
              placeholder="e.g. E-Commerce API"
              required
              autofocus
            />
          </div>

          <div class="form-group">
            <label class="form-label">Description (Optional)</label>
            <textarea
              v-model="newAppDesc"
              class="form-textarea"
              placeholder="Describe this mock workspace..."
              rows="3"
            ></textarea>
          </div>

          <div v-if="createError" class="modal__error">
            {{ createError }}
          </div>

          <div class="modal__footer">
            <button
              type="button"
              class="btn btn--ghost"
              @click="closeCreateModal"
            >
              Cancel
            </button>
            <button
              type="submit"
              class="btn btn--primary"
              :disabled="isCreating || !newAppName.trim()"
            >
              {{ isCreating ? 'Creating...' : 'Create' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard {
  max-width: 1000px;
  margin: 0 auto;
  padding: 2.5rem 1.5rem;
}

.dashboard__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.5rem;
  gap: 1rem;
}

.dashboard__title {
  font-size: 1.75rem;
  font-weight: 700;
  color: #f1f1f8;
  margin: 0 0 0.25rem;
}

.dashboard__subtitle {
  font-size: 0.875rem;
  color: #71718a;
  margin: 0;
}

.dashboard__search {
  margin-bottom: 2rem;
}

.search-input {
  width: 100%;
  padding: 0.625rem 1rem;
  background: #18181c;
  border: 1px solid #2a2a35;
  border-radius: 8px;
  color: #f1f1f8;
  font-size: 0.9375rem;
  outline: none;
}
.search-input:focus {
  border-color: #7c3aed;
}

.apps-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(310px, 1fr));
  gap: 1.25rem;
}

.app-card {
  background: #18181c;
  border: 1px solid #2a2a35;
  border-radius: 10px;
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.875rem;
  cursor: pointer;
  transition: transform 0.15s, border-color 0.15s;
}

.app-card:hover {
  transform: translateY(-2px);
  border-color: #3b3b4f;
}

.app-card__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 0.5rem;
}

.app-card__name {
  font-size: 1.125rem;
  font-weight: 600;
  color: #f1f1f8;
  margin: 0;
}

.app-card__slug {
  font-size: 0.75rem;
  color: #a78bfa;
  font-family: monospace;
}

.app-card__desc {
  font-size: 0.875rem;
  color: #8b8ba7;
  margin: 0;
  line-height: 1.4;
}

.app-card__stats {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8125rem;
  color: #71718a;
}

.stats--enabled {
  color: #34d399;
}

.app-card__actions {
  display: flex;
  gap: 0.5rem;
  margin-top: auto;
  padding-top: 0.5rem;
}

.badge {
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
}

.badge--success {
  background: rgba(52, 211, 153, 0.15);
  color: #34d399;
}

.badge--disabled {
  background: rgba(156, 163, 175, 0.15);
  color: #9ca3af;
}

.dashboard__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  border: 1px dashed #2a2a35;
  border-radius: 12px;
  text-align: center;
  gap: 0.75rem;
}

.empty-icon {
  font-size: 2.75rem;
}

.empty-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #f1f1f8;
}

.empty-desc {
  font-size: 0.875rem;
  color: #71718a;
  max-width: 380px;
  margin-bottom: 0.5rem;
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.65);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: #18181c;
  border: 1px solid #2a2a35;
  border-radius: 12px;
  padding: 1.75rem;
  width: 100%;
  max-width: 460px;
}

.modal__title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #f1f1f8;
  margin-bottom: 1.25rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
  margin-bottom: 1rem;
}

.form-label {
  font-size: 0.8125rem;
  font-weight: 500;
  color: #9999b3;
}

.form-input, .form-textarea {
  padding: 0.625rem 0.875rem;
  background: #0f0f11;
  border: 1px solid #2a2a35;
  border-radius: 8px;
  color: #f1f1f8;
  font-size: 0.9375rem;
  outline: none;
}

.form-input:focus, .form-textarea:focus {
  border-color: #7c3aed;
}

.modal__footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1.5rem;
}

.modal__error {
  color: #f87171;
  font-size: 0.875rem;
  margin-bottom: 0.75rem;
}

.btn {
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 0.15s;
}

.btn--sm {
  padding: 0.3rem 0.625rem;
  font-size: 0.8125rem;
}

.btn--primary {
  background: #7c3aed;
  color: #fff;
}
.btn--primary:hover:not(:disabled) {
  background: #6d28d9;
}

.btn--outline {
  background: transparent;
  border: 1px solid #2a2a35;
  color: #e8e8f0;
}
.btn--outline:hover {
  background: #2a2a35;
}

.btn--danger-outline {
  background: transparent;
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #f87171;
}
.btn--danger-outline:hover {
  background: rgba(239, 68, 68, 0.1);
}

.btn--ghost {
  background: transparent;
  color: #9999b3;
}
</style>
