<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { applicationService } from '@/services/applications'
import type { Application } from '@/types/application'
import type { AuthType } from '@/types/controller'

const route = useRoute()
const router = useRouter()
const appId = route.params.id as string

const loading = ref(true)
const saving = ref(false)
const app = ref<Application | null>(null)
const successMessage = ref('')
const errorMessage = ref('')

const form = reactive({
  name: '',
  description: '',
  is_enabled: true,
  auth_type: 'none' as AuthType,
  api_key_header: 'X-API-Key',
  api_key_value: '',
  bearer_token: '',
  basic_username: '',
  basic_password: '',
})

onMounted(async () => {
  try {
    const data = await applicationService.get(appId)
    app.value = data
    form.name = data.name
    form.description = data.description || ''
    form.is_enabled = data.is_enabled

    const auth = (data as any).auth_config
    if (auth) {
      form.auth_type = auth.auth_type || 'none'
      form.api_key_header = auth.api_key_header || 'X-API-Key'
      form.api_key_value = auth.api_key_value || ''
      form.bearer_token = auth.bearer_token || ''
      form.basic_username = auth.basic_username || ''
      form.basic_password = auth.basic_password || ''
    }
  } catch (err: any) {
    errorMessage.value = 'Failed to load application settings.'
  } finally {
    loading.value = false
  }
})

async function handleSave() {
  saving.value = true
  successMessage.value = ''
  errorMessage.value = ''

  try {
    const updatePayload: any = {
      name: form.name.trim(),
      description: form.description.trim() || undefined,
      is_enabled: form.is_enabled,
      auth_config: {
        auth_type: form.auth_type,
        api_key_header: form.auth_type === 'api_key' ? form.api_key_header : null,
        api_key_value: form.auth_type === 'api_key' ? form.api_key_value : null,
        bearer_token: form.auth_type === 'bearer' ? form.bearer_token : null,
        basic_username: form.auth_type === 'basic' ? form.basic_username : null,
        basic_password: form.auth_type === 'basic' ? form.basic_password : null,
      },
    }

    const updated = await applicationService.update(appId, updatePayload)
    app.value = updated
    successMessage.value = 'Settings saved successfully!'
  } catch (err: any) {
    errorMessage.value = err?.response?.data?.detail || 'Failed to update settings.'
  } finally {
    saving.value = false
  }
}

import ConfirmDialog from '@/components/ConfirmDialog.vue'
const showDeleteConfirm = ref(false)
const isDeleting = ref(false)

async function confirmDelete() {
  isDeleting.value = true
  try {
    await applicationService.delete(appId)
    router.push({ name: 'dashboard' })
  } catch {
    alert('Failed to delete application.')
  } finally {
    isDeleting.value = false
  }
}
</script>

<template>
  <div class="settings-page">
    <div class="settings-page__header">
      <div class="header-left">
        <RouterLink :to="`/apps/${appId}`" class="back-link">← Back to Workspace</RouterLink>
        <h1 class="settings-title">Application Settings</h1>
      </div>
      <button class="btn btn--primary" :disabled="saving" @click="handleSave">
        {{ saving ? 'Saving...' : 'Save Changes' }}
      </button>
    </div>

    <div v-if="loading" class="loading-state">Loading settings...</div>

    <div v-else class="settings-container">
      <div v-if="successMessage" class="alert alert--success">{{ successMessage }}</div>
      <div v-if="errorMessage" class="alert alert--danger">{{ errorMessage }}</div>

      <!-- General Section -->
      <section class="settings-card">
        <h2 class="card-title">General Information</h2>
        <p class="card-subtitle">Configure the application metadata and global operational status.</p>

        <div class="form-group">
          <label class="form-label">Application Name</label>
          <input v-model="form.name" type="text" class="form-input" required />
        </div>

        <div class="form-group">
          <label class="form-label">Slug (Identifier)</label>
          <input :value="app?.slug" type="text" class="form-input disabled" disabled />
          <span class="field-hint">Used in your public mock endpoint URLs: <code>/mock/{{ app?.slug }}/...</code></span>
        </div>

        <div class="form-group">
          <label class="form-label">Description</label>
          <textarea v-model="form.description" class="form-textarea" rows="3"></textarea>
        </div>

        <div class="form-check">
          <label class="toggle-switch">
            <input v-model="form.is_enabled" type="checkbox" />
            <span class="toggle-slider"></span>
          </label>
          <div>
            <div class="check-title">Application Enabled</div>
            <div class="check-subtitle">When disabled, all endpoints under this application return HTTP 503.</div>
          </div>
        </div>
      </section>

      <!-- Global Authentication Section -->
      <section class="settings-card">
        <h2 class="card-title">Application Authentication</h2>
        <p class="card-subtitle">Default security rules applied to all endpoints unless overridden by a controller or API.</p>

        <div class="form-group">
          <label class="form-label">Authentication Type</label>
          <select v-model="form.auth_type" class="form-select">
            <option value="none">No Authentication (Public)</option>
            <option value="api_key">API Key (Header)</option>
            <option value="bearer">Bearer Token (JWT / Secret)</option>
            <option value="basic">HTTP Basic Authentication</option>
          </select>
        </div>

        <!-- API Key Options -->
        <div v-if="form.auth_type === 'api_key'" class="auth-subform">
          <div class="form-group">
            <label class="form-label">Header Name</label>
            <input v-model="form.api_key_header" type="text" class="form-input" placeholder="X-API-Key" />
          </div>
          <div class="form-group">
            <label class="form-label">Expected Key Value</label>
            <input v-model="form.api_key_value" type="text" class="form-input" placeholder="secret-key-value" />
          </div>
        </div>

        <!-- Bearer Token Options -->
        <div v-if="form.auth_type === 'bearer'" class="auth-subform">
          <div class="form-group">
            <label class="form-label">Expected Bearer Token</label>
            <input v-model="form.bearer_token" type="text" class="form-input" placeholder="my-secret-bearer-token" />
          </div>
        </div>

        <!-- Basic Auth Options -->
        <div v-if="form.auth_type === 'basic'" class="auth-subform">
          <div class="form-row">
            <div class="form-group flex-1">
              <label class="form-label">Username</label>
              <input v-model="form.basic_username" type="text" class="form-input" placeholder="admin" />
            </div>
            <div class="form-group flex-1">
              <label class="form-label">Password</label>
              <input v-model="form.basic_password" type="password" class="form-input" placeholder="••••••••" />
            </div>
          </div>
        </div>
      </section>

      <!-- Danger Zone -->
      <section class="settings-card card--danger">
        <h2 class="card-title text-danger">Danger Zone</h2>
        <p class="card-subtitle">Irreversible actions that affect this entire mock application.</p>
        <div class="danger-row">
          <div>
            <div class="check-title">Delete Application</div>
            <div class="check-subtitle">Permanently delete this application and all associated controllers and endpoints.</div>
          </div>
          <button class="btn btn--danger" @click="showDeleteConfirm = true">Delete Application</button>
        </div>
      </section>

      <!-- Delete Confirmation Dialog -->
      <ConfirmDialog
        :show="showDeleteConfirm"
        title="Delete Application"
        :message="`Are you sure you want to permanently delete '${app?.name}'? This action cannot be undone.`"
        confirm-text="Delete Permanently"
        variant="danger"
        :loading="isDeleting"
        @confirm="confirmDelete"
        @cancel="showDeleteConfirm = false"
      />
    </div>
  </div>
</template>

<style scoped>
.settings-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 2rem 1.5rem 4rem;
}

.settings-page__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 2rem;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.back-link {
  color: #71718a;
  text-decoration: none;
  font-size: 0.875rem;
}
.back-link:hover {
  color: #f1f1f8;
}

.settings-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #f1f1f8;
  margin: 0;
}

.settings-container {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.settings-card {
  background: #141418;
  border: 1px solid #2a2a35;
  border-radius: 12px;
  padding: 1.5rem;
}

.card-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #f1f1f8;
  margin: 0 0 0.25rem;
}

.card-subtitle {
  font-size: 0.875rem;
  color: #71718a;
  margin: 0 0 1.25rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
  margin-bottom: 1.25rem;
}

.form-row {
  display: flex;
  gap: 1rem;
}

.flex-1 {
  flex: 1;
}

.form-label {
  font-size: 0.8125rem;
  font-weight: 500;
  color: #9999b3;
}

.form-input, .form-textarea {
  padding: 0.625rem 0.875rem;
  background: #18181c;
  border: 1px solid #2a2a35;
  border-radius: 8px;
  color: #f1f1f8;
  font-size: 0.9375rem;
  outline: none;
  transition: border-color 0.15s;
}

.form-select {
  padding: 0.625rem 2.25rem 0.625rem 0.875rem;
  background-color: #18181c;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%2371718a' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 0.75rem center;
  background-size: 16px 16px;
  border: 1px solid #2a2a35;
  border-radius: 8px;
  color: #f1f1f8;
  font-size: 0.9375rem;
  outline: none;
  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;
  cursor: pointer;
  transition: border-color 0.15s;
}

.form-input:focus, .form-textarea:focus {
  border-color: #7c3aed;
}

.form-select:focus {
  border-color: #7c3aed;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%23a78bfa' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
}

.form-input.disabled {
  background: #0f0f11;
  color: #71718a;
  cursor: not-allowed;
}

.field-hint {
  font-size: 0.75rem;
  color: #71718a;
}

.field-hint code {
  color: #a78bfa;
}

.form-check {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: #18181c;
  border-radius: 8px;
}

.check-title {
  font-size: 0.9375rem;
  font-weight: 500;
  color: #f1f1f8;
}

.check-subtitle {
  font-size: 0.8125rem;
  color: #71718a;
}

/* Toggle Switch */
.toggle-switch {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
}

.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #2a2a35;
  transition: 0.2s;
  border-radius: 24px;
}

.toggle-slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: 0.2s;
  border-radius: 50%;
}

input:checked + .toggle-slider {
  background-color: #7c3aed;
}

input:checked + .toggle-slider:before {
  transform: translateX(20px);
}

.auth-subform {
  padding: 1rem;
  background: #18181c;
  border: 1px solid #2a2a35;
  border-radius: 8px;
  margin-top: 0.5rem;
}

.card--danger {
  border-color: rgba(239, 68, 68, 0.25);
}

.text-danger {
  color: #f87171;
}

.danger-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 0.5rem;
}

.alert {
  padding: 0.75rem 1rem;
  border-radius: 8px;
  font-size: 0.875rem;
}

.alert--success {
  background: rgba(52, 211, 153, 0.1);
  border: 1px solid rgba(52, 211, 153, 0.3);
  color: #34d399;
}

.alert--danger {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #f87171;
}

.btn {
  padding: 0.5rem 1.25rem;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 0.15s;
}

.btn--primary {
  background: #7c3aed;
  color: #fff;
}
.btn--primary:hover:not(:disabled) {
  background: #6d28d9;
}
.btn--primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn--danger {
  background: #dc2626;
  color: #fff;
}
.btn--danger:hover {
  background: #b91c1c;
}
</style>
