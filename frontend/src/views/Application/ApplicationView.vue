<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Settings,
  Play,
  Sliders,
  Terminal,
  Sparkles,
  AlertCircle,
  ArrowLeft,
  Plus,
  Copy,
  Save,
  Download,
  Upload,
  ChevronDown,
  FileCode,
} from '@lucide/vue'
import { applicationService } from '@/services/applications'
import { controllerService } from '@/services/controllers'
import { endpointService } from '@/services/endpoints'
import EndpointPlayground from '@/components/EndpointPlayground.vue'
import ImportSpecModal from '@/components/ImportSpecModal.vue'
import { validateJsonWithMacros, formatJsonWithMacros } from '@/utils/jsonMacroHelper'
import type { Application } from '@/types/application'
import type { Controller } from '@/types/controller'
import type { ApiEndpoint, HttpMethod } from '@/types/endpoint'

const route = useRoute()
const router = useRouter()
const appId = route.params.id as string

const app = ref<Application | null>(null)
const controllers = ref<Controller[]>([])
const selectedController = ref<Controller | null>(null)
const endpoints = ref<ApiEndpoint[]>([])
const selectedEndpoint = ref<ApiEndpoint | null>(null)

const loading = ref(true)
const showCreateCtrl = ref(false)
const newCtrlName = ref('')
const newCtrlDesc = ref('')

const showCreateEndpoint = ref(false)
const newEpName = ref('')
const newEpMethod = ref<HttpMethod>('GET')
const newEpPath = ref('')
const newEpStatus = ref(200)
const newEpBody = ref('{\n  "message": "Hello from mock"\n}')

// Tabs & Toast state
const activeTab = ref<'editor' | 'playground'>('editor')
const toastMessage = ref<string | null>(null)
let toastTimer: ReturnType<typeof setTimeout> | null = null

function showToast(msg: string) {
  toastMessage.value = msg
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => {
    toastMessage.value = null
  }, 2500)
}

// JSON Editor State & Real-time Validation
const bodyText = ref('')
const jsonError = ref<string | null>(null)

function validateBodyText(text: string) {
  jsonError.value = validateJsonWithMacros(text)
}

function handleBodyInput(e: Event) {
  const val = (e.target as HTMLTextAreaElement).value
  bodyText.value = val
  validateBodyText(val)
}

function handleTabKey(e: KeyboardEvent) {
  const textarea = e.target as HTMLTextAreaElement
  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  bodyText.value = bodyText.value.substring(0, start) + '  ' + bodyText.value.substring(end)
  setTimeout(() => {
    textarea.selectionStart = textarea.selectionEnd = start + 2
  }, 0)
  validateBodyText(bodyText.value)
}

function beautifyJson() {
  if (!bodyText.value.trim()) return
  const res = formatJsonWithMacros(bodyText.value)
  if (res.error) {
    jsonError.value = res.error
  } else {
    bodyText.value = res.formatted
    jsonError.value = null
  }
}

function insertMacro(macro: string) {
  bodyText.value += (bodyText.value.length ? ' ' : '') + macro
  validateBodyText(bodyText.value)
}

const methodColors: Record<HttpMethod, string> = {
  GET: '#10b981',
  POST: '#3b82f6',
  PUT: '#f59e0b',
  PATCH: '#8b5cf6',
  DELETE: '#ef4444',
  HEAD: '#6b7280',
  OPTIONS: '#6b7280',
}

onMounted(async () => {
  await loadApplication()
  await loadControllers()
  loading.value = false
})

async function loadApplication() {
  try {
    app.value = await applicationService.get(appId)
  } catch {
    router.push({ name: 'dashboard' })
  }
}

async function loadControllers() {
  controllers.value = await controllerService.list(appId)
  if (controllers.value.length > 0 && !selectedController.value) {
    selectController(controllers.value[0]!)
  }
}

async function selectController(ctrl: Controller) {
  selectedController.value = ctrl
  selectedEndpoint.value = null
  await loadEndpoints(ctrl.id)
}

async function loadEndpoints(ctrlId: string) {
  endpoints.value = await endpointService.list(ctrlId)
  if (endpoints.value.length > 0 && !selectedEndpoint.value) {
    selectEndpoint(endpoints.value[0]!)
  }
}

function selectEndpoint(ep: ApiEndpoint) {
  selectedEndpoint.value = ep
  if (typeof ep.response_body === 'object' && ep.response_body !== null) {
    bodyText.value = JSON.stringify(ep.response_body, null, 2)
  } else {
    bodyText.value = String(ep.response_body || '')
  }
  validateBodyText(bodyText.value)
}

async function handleCreateController() {
  if (!newCtrlName.value.trim()) return
  const created = await controllerService.create(appId, {
    name: newCtrlName.value.trim(),
    description: newCtrlDesc.value.trim() || undefined,
  })
  controllers.value.push(created)
  newCtrlName.value = ''
  newCtrlDesc.value = ''
  showCreateCtrl.value = false
  selectController(created)
  showToast('Controller created successfully')
}

async function handleCreateEndpoint() {
  if (!selectedController.value || !newEpName.value.trim() || !newEpPath.value.trim()) return

  let parsedBody: unknown = null
  try {
    parsedBody = JSON.parse(newEpBody.value)
  } catch {
    parsedBody = newEpBody.value
  }

  const created = await endpointService.create(selectedController.value.id, {
    name: newEpName.value.trim(),
    method: newEpMethod.value,
    path: newEpPath.value.trim(),
    response_status: Number(newEpStatus.value),
    response_body: parsedBody as Record<string, unknown> | null,
  })

  endpoints.value.push(created)
  newEpName.value = ''
  newEpPath.value = ''
  showCreateEndpoint.value = false
  selectEndpoint(created)
  showToast('Endpoint created successfully')
}

async function toggleEndpoint(ep: ApiEndpoint, e: Event) {
  e.stopPropagation()
  const updated = await endpointService.toggle(ep.id)
  ep.is_enabled = updated.is_enabled
}

async function saveSelectedEndpoint() {
  if (!selectedEndpoint.value) return
  let bodyData: Record<string, unknown> | string = bodyText.value
  try {
    const parsed = JSON.parse(bodyText.value)
    if (parsed && typeof parsed === 'object') {
      bodyData = parsed as Record<string, unknown>
    }
  } catch {
    // Keep as string
  }

  const updated = await endpointService.update(selectedEndpoint.value.id, {
    name: selectedEndpoint.value.name,
    method: selectedEndpoint.value.method,
    path: selectedEndpoint.value.path,
    response_status: Number(selectedEndpoint.value.response_status),
    response_delay_ms: Number(selectedEndpoint.value.response_delay_ms),
    auth_inherit: selectedEndpoint.value.auth_inherit,
    response_body: bodyData,
  })
  selectedEndpoint.value = updated
  showToast('Endpoint saved successfully!')
}

const mockUrl = computed(() => {
  if (!app.value || !selectedEndpoint.value) return ''
  const origin = window.location.origin
  const path = selectedEndpoint.value.path.startsWith('/')
    ? selectedEndpoint.value.path.slice(1)
    : selectedEndpoint.value.path
  return `${origin}/mock/${app.value.slug}/${path}`
})

async function copyToClipboard(text: string, label: string) {
  await navigator.clipboard.writeText(text)
  showToast(`${label} copied to clipboard!`)
}

// Export & Import Specification logic
const showExportMenu = ref(false)
const isExporting = ref(false)
const showImportModal = ref(false)

function downloadJson(filename: string, data: Record<string, unknown>) {
  const jsonStr = JSON.stringify(data, null, 2)
  const blob = new Blob([jsonStr], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

async function handleExportOpenApi() {
  if (!app.value) return
  showExportMenu.value = false
  isExporting.value = true
  try {
    const spec = await applicationService.exportOpenApi(app.value.id)
    downloadJson(`${app.value.slug}-openapi.json`, spec)
    showToast('OpenAPI 3.0 specification exported successfully!')
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string } } }
    showToast(e?.response?.data?.detail ?? 'Failed to export OpenAPI')
  } finally {
    isExporting.value = false
  }
}

async function handleExportPostman() {
  if (!app.value) return
  showExportMenu.value = false
  isExporting.value = true
  try {
    const spec = await applicationService.exportPostman(app.value.id)
    downloadJson(`${app.value.slug}-postman-collection.json`, spec)
    showToast('Postman collection exported successfully!')
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string } } }
    showToast(e?.response?.data?.detail ?? 'Failed to export Postman collection')
  } finally {
    isExporting.value = false
  }
}

async function handleImportIntoApp(data: { spec: string }) {
  if (!app.value) return
  try {
    await applicationService.importIntoApplication(app.value.id, { spec: data.spec })
    showImportModal.value = false
    await loadControllers()
    showToast('Endpoints successfully imported and merged!')
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string } } }
    showToast(e?.response?.data?.detail ?? 'Failed to import specification')
  }
}
</script>

<template>
  <div v-if="loading" class="loading-state">
    <div class="spinner"></div>
    <span>Loading workspace...</span>
  </div>
  <div v-else-if="app" class="workspace">
    <!-- Toast Notification -->
    <div v-if="toastMessage" class="toast-popup">
      {{ toastMessage }}
    </div>

    <!-- Workspace Top Bar -->
    <div class="workspace__topbar">
      <div class="topbar-left">
        <RouterLink to="/" class="back-link">
          <ArrowLeft :size="14" class="btn-icon" />
          <span>Applications</span>
        </RouterLink>
        <h1 class="workspace-title">{{ app.name }}</h1>
        <span class="base-badge">/mock/{{ app.slug }}</span>
      </div>
      <div class="topbar-right">
        <button
          class="btn btn--outline"
          @click="showImportModal = true"
        >
          <Upload :size="14" class="btn-icon" />
          <span>Import Spec</span>
        </button>

        <div class="dropdown-wrapper">
          <button
            class="btn btn--outline"
            :disabled="isExporting"
            @click="showExportMenu = !showExportMenu"
          >
            <Download :size="14" class="btn-icon" />
            <span>{{ isExporting ? 'Exporting...' : 'Export' }}</span>
            <ChevronDown :size="12" class="chevron-icon" />
          </button>

          <div v-if="showExportMenu" class="dropdown-menu" @click="showExportMenu = false">
            <button class="dropdown-item" @click="handleExportOpenApi">
              <FileCode :size="14" class="item-icon" />
              <span>OpenAPI 3.0 (JSON)</span>
            </button>
            <button class="dropdown-item" @click="handleExportPostman">
              <FileCode :size="14" class="item-icon" />
              <span>Postman Collection (JSON)</span>
            </button>
          </div>
        </div>

        <button
          class="btn btn--outline"
          @click="router.push({ name: 'application-settings', params: { id: app.id } })"
        >
          <Settings :size="14" class="btn-icon" />
          <span>Settings</span>
        </button>
      </div>
    </div>

    <!-- Workspace Main Layout -->
    <div class="workspace__grid">
      <!-- Controllers Sidebar Column -->
      <aside class="sidebar-col">
        <div class="col-header">
          <span class="col-title">Controllers</span>
          <button class="btn btn--sm btn--primary" title="Add Controller" @click="showCreateCtrl = true">
            <Plus :size="14" />
          </button>
        </div>

        <div v-if="controllers.length === 0" class="col-empty">
          No controllers yet.
        </div>
        <div
          v-for="ctrl in controllers"
          :key="ctrl.id"
          class="ctrl-item"
          :class="{ 'ctrl-item--active': selectedController?.id === ctrl.id }"
          @click="selectController(ctrl)"
        >
          <div class="ctrl-item__name">{{ ctrl.name }}</div>
          <span class="ctrl-item__count">{{ ctrl.endpoint_count ?? 0 }}</span>
        </div>
      </aside>

      <!-- Endpoints Middle Column -->
      <section class="endpoints-col">
        <div class="col-header">
          <span class="col-title">{{ selectedController?.name ?? 'Endpoints' }}</span>
          <button
            v-if="selectedController"
            class="btn btn--sm btn--primary"
            @click="showCreateEndpoint = true"
          >
            <Plus :size="14" class="btn-icon" />
            <span>New API</span>
          </button>
        </div>

        <div v-if="endpoints.length === 0" class="col-empty">
          No endpoints defined for this controller.
        </div>
        <div
          v-for="ep in endpoints"
          :key="ep.id"
          class="ep-item"
          :class="{ 'ep-item--active': selectedEndpoint?.id === ep.id }"
          @click="selectEndpoint(ep)"
        >
          <span
            class="method-pill"
            :style="{ color: methodColors[ep.method] }"
          >
            {{ ep.method }}
          </span>
          <span class="ep-item__path">{{ ep.path }}</span>
          <input
            type="checkbox"
            :checked="ep.is_enabled"
            class="ep-item__toggle"
            title="Enable / Disable Endpoint"
            @change="toggleEndpoint(ep, $event)"
          />
        </div>
      </section>

      <!-- Detail / Editor Column -->
      <main class="editor-col">
        <div v-if="!selectedEndpoint" class="no-selection">
          Select or create an endpoint to view details, edit responses, and test live.
        </div>
        <div v-else class="endpoint-detail">
          <!-- Endpoint Meta Bar -->
          <div class="detail-header">
            <div class="detail-path-bar">
              <span
                class="method-pill-large"
                :style="{ color: methodColors[selectedEndpoint.method] }"
              >
                {{ selectedEndpoint.method }}
              </span>
              <span class="detail-path">{{ selectedEndpoint.path }}</span>
            </div>
            <div class="detail-actions">
              <button
                class="btn btn--sm"
                :class="activeTab === 'playground' ? 'btn--primary' : 'btn--outline'"
                @click="activeTab = 'playground'"
              >
                <Play :size="13" class="btn-icon" />
                <span>Live Tester</span>
              </button>
              <button class="btn btn--sm btn--outline" @click="copyToClipboard(mockUrl, 'Mock URL')">
                <Copy :size="13" class="btn-icon" />
                <span>Copy URL</span>
              </button>
              <button class="btn btn--sm btn--primary" @click="saveSelectedEndpoint">
                <Save :size="13" class="btn-icon" />
                <span>Save</span>
              </button>
            </div>
          </div>

          <!-- URL Display Banner -->
          <div class="mock-url-box">
            <span class="mock-url-label">Mock Base:</span>
            <code class="mock-url-code">{{ mockUrl }}</code>
          </div>

          <!-- View Tabs (Configuration / Playground) -->
          <div class="tab-bar">
            <button
              class="tab-btn"
              :class="{ 'tab-btn--active': activeTab === 'editor' }"
              @click="activeTab = 'editor'"
            >
              <Sliders :size="14" class="tab-icon" />
              <span>Response Configuration</span>
            </button>
            <button
              class="tab-btn"
              :class="{ 'tab-btn--active': activeTab === 'playground' }"
              @click="activeTab = 'playground'"
            >
              <Terminal :size="14" class="tab-icon" />
              <span>Playground & Snippets</span>
            </button>
          </div>

          <!-- 1. Configuration Tab -->
          <div v-if="activeTab === 'editor'" class="tab-content">
            <div class="form-row">
              <div class="form-group flex-1">
                <label class="form-label">HTTP Status Code</label>
                <input
                  v-model.number="selectedEndpoint.response_status"
                  type="number"
                  class="form-input"
                />
              </div>
              <div class="form-group flex-1">
                <label class="form-label">Response Delay (ms)</label>
                <input
                  v-model.number="selectedEndpoint.response_delay_ms"
                  type="number"
                  class="form-input"
                />
              </div>
              <div class="form-group flex-1">
                <label class="form-label">Auth Inheritance</label>
                <select v-model="selectedEndpoint.auth_inherit" class="form-select">
                  <option value="inherit">Inherit</option>
                  <option value="override_on">Override: Enabled</option>
                  <option value="override_off">Override: Disabled (Public)</option>
                </select>
              </div>
            </div>

            <div class="form-group">
              <div class="json-header">
                <div class="json-header__left">
                  <label class="form-label">Response Body (JSON / Template)</label>
                  <div class="macro-tags">
                    <span class="macro-tag" v-text="'{{uuid}}'" @click="insertMacro('{{uuid}}')"></span>
                    <span class="macro-tag" v-text="'{{timestamp}}'" @click="insertMacro('{{timestamp}}')"></span>
                    <span class="macro-tag" v-text="'{{random.name}}'" @click="insertMacro('{{random.name}}')"></span>
                    <span class="macro-tag" v-text="'{{random.email}}'" @click="insertMacro('{{random.email}}')"></span>
                    <span class="macro-tag" v-text="'{{request.query.param}}'" @click="insertMacro('{{request.query.param}}')"></span>
                  </div>
                </div>
                <button
                  type="button"
                  class="btn btn--sm btn--outline beautify-btn"
                  @click="beautifyJson"
                >
                  <Sparkles :size="13" class="btn-icon" />
                  <span>Beautify JSON</span>
                </button>
              </div>

              <textarea
                :value="bodyText"
                class="form-textarea code-area"
                :class="{ 'code-area--error': !!jsonError }"
                rows="13"
                spellcheck="false"
                autocomplete="off"
                autocapitalize="off"
                autocorrect="off"
                placeholder='{\n  "status": "success",\n  "id": "{{uuid}}"\n}'
                @keydown.tab.prevent="handleTabKey"
                @input="handleBodyInput"
              ></textarea>

              <div v-if="jsonError" class="json-error-banner">
                <AlertCircle :size="14" class="error-icon" />
                <span class="error-text">JSON Syntax Error: {{ jsonError }}</span>
              </div>
            </div>
          </div>

          <!-- 2. Interactive Playground Tab -->
          <div v-else-if="activeTab === 'playground'" class="tab-content">
            <EndpointPlayground
              :endpoint="selectedEndpoint"
              :app-slug="app.slug"
            />
          </div>
        </div>
      </main>
    </div>

    <!-- Create Controller Modal -->
    <div v-if="showCreateCtrl" class="modal-backdrop" @click.self="showCreateCtrl = false">
      <div class="modal">
        <h2 class="modal__title">Create Controller</h2>
        <form @submit.prevent="handleCreateController">
          <div class="form-group">
            <label class="form-label">Controller Name</label>
            <input
              v-model="newCtrlName"
              type="text"
              class="form-input"
              placeholder="e.g. Users, Orders, Payments"
              required
              autofocus
            />
          </div>
          <div class="modal__footer">
            <button type="button" class="btn btn--ghost" @click="showCreateCtrl = false">Cancel</button>
            <button type="submit" class="btn btn--primary">Create</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Create Endpoint Modal -->
    <div v-if="showCreateEndpoint" class="modal-backdrop" @click.self="showCreateEndpoint = false">
      <div class="modal">
        <h2 class="modal__title">Create API Endpoint</h2>
        <form @submit.prevent="handleCreateEndpoint">
          <div class="form-group">
            <label class="form-label">Endpoint Name</label>
            <input
              v-model="newEpName"
              type="text"
              class="form-input"
              placeholder="e.g. Get User by ID"
              required
            />
          </div>

          <div class="form-row">
            <div class="form-group flex-1">
              <label class="form-label">HTTP Method</label>
              <select v-model="newEpMethod" class="form-select">
                <option value="GET">GET</option>
                <option value="POST">POST</option>
                <option value="PUT">PUT</option>
                <option value="PATCH">PATCH</option>
                <option value="DELETE">DELETE</option>
              </select>
            </div>
            <div class="form-group flex-2">
              <label class="form-label">Path</label>
              <input
                v-model="newEpPath"
                type="text"
                class="form-input"
                placeholder="/users/{id}"
                required
              />
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">Initial Response JSON</label>
            <textarea
              v-model="newEpBody"
              class="form-textarea code-area"
              rows="6"
            ></textarea>
          </div>

          <div class="modal__footer">
            <button type="button" class="btn btn--ghost" @click="showCreateEndpoint = false">Cancel</button>
            <button type="submit" class="btn btn--primary">Create API</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Import Specification Modal -->
    <ImportSpecModal
      :show="showImportModal"
      :target-app-id="app.id"
      :target-app-name="app.name"
      @close="showImportModal = false"
      @imported="handleImportIntoApp"
    />
  </div>
</template>

<style scoped>
.workspace {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 60px);
  background: var(--bg-app, #09090b);
  color: var(--text-main, #f4f4f7);
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.dropdown-wrapper {
  position: relative;
}

.dropdown-menu {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  background: var(--bg-surface-elevated, #181820);
  border: 1px solid var(--border-subtle, #22222e);
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
  padding: 0.35rem;
  z-index: 100;
  min-width: 210px;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  font-size: 0.8125rem;
  color: var(--text-main, #f4f4f7);
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  text-align: left;
  transition: all var(--transition-fast, 0.15s);
  width: 100%;
}

.dropdown-item:hover {
  background: rgba(255, 255, 255, 0.06);
  color: #fff;
}

.chevron-icon {
  margin-left: 0.25rem;
}

.item-icon {
  color: var(--primary, #7c3aed);
}

.toast-popup {
  position: fixed;
  bottom: 1.5rem;
  right: 1.5rem;
  background: var(--bg-surface-elevated, #181820);
  color: var(--text-main, #f4f4f7);
  border: 1px solid var(--primary, #7c3aed);
  box-shadow: 0 4px 16px var(--primary-glow, rgba(124, 58, 237, 0.25));
  padding: 0.625rem 1.25rem;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 600;
  z-index: 2000;
  animation: slideUp 0.2s ease-out;
}

@keyframes slideUp {
  from {
    transform: translateY(10px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.workspace__topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1.75rem;
  background: var(--bg-surface, #121217);
  border-bottom: 1px solid var(--border-subtle, #22222e);
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  color: var(--text-muted, #9494a8);
  text-decoration: none;
  font-size: 0.875rem;
  transition: color var(--transition-fast, 0.15s);
}
.back-link:hover {
  color: var(--text-main, #f4f4f7);
}

.workspace-title {
  font-size: 1.25rem;
  font-weight: 700;
  margin: 0;
}

.base-badge {
  font-family: monospace;
  font-size: 0.8125rem;
  background: var(--bg-surface-elevated, #181820);
  color: var(--primary, #7c3aed);
  border: 1px solid var(--border-subtle, #22222e);
  padding: 0.2rem 0.6rem;
  border-radius: 6px;
}

.workspace__grid {
  display: grid;
  grid-template-columns: 240px 300px 1fr;
  flex: 1;
  overflow: hidden;
}

.sidebar-col, .endpoints-col {
  background: var(--bg-surface, #121217);
  border-right: 1px solid var(--border-subtle, #22222e);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.col-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.875rem 1rem;
  border-bottom: 1px solid var(--border-subtle, #22222e);
}

.col-title {
  font-size: 0.8125rem;
  font-weight: 600;
  text-transform: uppercase;
  color: var(--text-muted, #9494a8);
  letter-spacing: 0.05em;
}

.ctrl-item, .ep-item {
  display: flex;
  align-items: center;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--border-subtle, #22222e);
  cursor: pointer;
  transition: background var(--transition-fast, 0.15s);
}

.ctrl-item:hover, .ep-item:hover {
  background: var(--bg-surface-hover, #21212c);
}

.ctrl-item--active, .ep-item--active {
  background: var(--bg-surface-elevated, #181820);
  border-left: 3px solid var(--primary, #7c3aed);
}

.ctrl-item__name {
  flex: 1;
  font-size: 0.9375rem;
  font-weight: 500;
}

.ctrl-item__count {
  font-size: 0.75rem;
  background: var(--bg-surface-elevated, #181820);
  padding: 0.15rem 0.45rem;
  border-radius: 999px;
  color: var(--text-muted, #9494a8);
  border: 1px solid var(--border-subtle, #22222e);
}

.method-pill {
  font-size: 0.75rem;
  font-weight: 700;
  font-family: monospace;
  width: 50px;
}

.ep-item__path {
  flex: 1;
  font-size: 0.875rem;
  font-family: monospace;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ep-item__toggle {
  accent-color: var(--primary, #7c3aed);
  cursor: pointer;
}

.editor-col {
  background: var(--bg-app, #09090b);
  padding: 1.5rem;
  overflow-y: auto;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.detail-path-bar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.method-pill-large {
  font-size: 1.125rem;
  font-weight: 800;
  font-family: monospace;
}

.detail-path {
  font-size: 1.25rem;
  font-weight: 600;
  font-family: monospace;
}

.detail-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.mock-url-box {
  background: var(--bg-surface, #121217);
  border: 1px solid var(--border-subtle, #22222e);
  border-radius: 8px;
  padding: 0.625rem 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.mock-url-label {
  font-size: 0.8125rem;
  color: var(--text-muted, #9494a8);
}

.mock-url-code {
  color: var(--success, #10b981);
  font-family: monospace;
  font-size: 0.875rem;
}

.tab-bar {
  display: flex;
  border-bottom: 1px solid var(--border-subtle, #22222e);
  margin-bottom: 1.5rem;
  gap: 0.5rem;
}

.tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--text-muted, #9494a8);
  padding: 0.625rem 1.25rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast, 0.15s);
}

.tab-btn:hover {
  color: var(--text-main, #f4f4f7);
}

.tab-btn--active {
  color: var(--primary, #7c3aed);
  border-bottom-color: var(--primary, #7c3aed);
  font-weight: 600;
}

.tab-icon {
  flex-shrink: 0;
}

.code-area {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.875rem;
  line-height: 1.5;
}

.json-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 0.5rem;
  gap: 1rem;
}

.json-header__left {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.macro-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem;
  align-items: center;
}

.macro-tag {
  background: var(--bg-surface-elevated, #181820);
  color: var(--primary, #7c3aed);
  font-family: monospace;
  font-size: 0.6875rem;
  padding: 0.15rem 0.45rem;
  border-radius: 4px;
  border: 1px solid var(--border-subtle, #22222e);
  cursor: pointer;
  user-select: none;
  transition: all var(--transition-fast, 0.15s);
}

.macro-tag:hover {
  background: var(--bg-surface-hover, #21212c);
  border-color: var(--primary, #7c3aed);
}

.beautify-btn {
  font-size: 0.75rem;
  white-space: nowrap;
}

.code-area--error {
  border-color: var(--danger, #ef4444) !important;
  box-shadow: 0 0 0 1px var(--danger-border, rgba(239, 68, 68, 0.25));
}

.json-error-banner {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: var(--danger-bg, rgba(239, 68, 68, 0.1));
  border: 1px solid var(--danger-border, rgba(239, 68, 68, 0.3));
  border-radius: 6px;
}

.error-icon {
  flex-shrink: 0;
  color: var(--danger, #ef4444);
}

.error-text {
  color: var(--danger, #ef4444);
  font-size: 0.8125rem;
  font-family: monospace;
}

.form-row {
  display: flex;
  gap: 1rem;
}

.flex-1 { flex: 1; }
.flex-2 { flex: 2; }

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
  margin-bottom: 1rem;
}

.form-label {
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--text-muted, #9494a8);
}

.form-input, .form-textarea {
  padding: 0.625rem 0.875rem;
  background: var(--bg-surface, #121217);
  border: 1px solid var(--border-subtle, #22222e);
  border-radius: 8px;
  color: var(--text-main, #f4f4f7);
  font-size: 0.9375rem;
  outline: none;
  transition: border-color var(--transition-fast, 0.15s);
}

.form-input:focus, .form-textarea:focus {
  border-color: var(--border-focus, #8b5cf6);
}

.form-select {
  padding: 0.625rem 2.25rem 0.625rem 0.875rem;
  background-color: var(--bg-surface, #121217);
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%2371718a' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 0.75rem center;
  background-size: 16px 16px;
  border: 1px solid var(--border-subtle, #22222e);
  border-radius: 8px;
  color: var(--text-main, #f4f4f7);
  font-size: 0.9375rem;
  outline: none;
  appearance: none;
  cursor: pointer;
  transition: border-color var(--transition-fast, 0.15s);
}

.form-select:focus {
  border-color: var(--border-focus, #8b5cf6);
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
  background: var(--bg-surface, #121217);
  border: 1px solid var(--border-subtle, #22222e);
  border-radius: 12px;
  padding: 1.75rem;
  width: 100%;
  max-width: 460px;
  box-shadow: var(--shadow-lg);
}

.modal__title {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-main, #f4f4f7);
  margin-bottom: 1.25rem;
}

.modal__footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1.5rem;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.375rem;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all var(--transition-fast, 0.15s);
}

.btn-icon {
  flex-shrink: 0;
}

.btn--sm {
  padding: 0.35rem 0.65rem;
  font-size: 0.8125rem;
}

.btn--primary {
  background: var(--primary, #7c3aed);
  color: #fff;
}
.btn--primary:hover:not(:disabled) {
  background: var(--primary-hover, #6d28d9);
}

.btn--outline {
  background: transparent;
  border: 1px solid var(--border-subtle, #22222e);
  color: var(--text-main, #f4f4f7);
}
.btn--outline:hover {
  background: var(--bg-surface-hover, #21212c);
  border-color: var(--border-strong, #323242);
}

.btn--ghost {
  background: transparent;
  color: var(--text-muted, #9494a8);
}
.btn--ghost:hover {
  color: var(--text-main, #f4f4f7);
}

.col-empty, .no-selection, .loading-state {
  padding: 2rem 1rem;
  text-align: center;
  color: var(--text-muted, #9494a8);
  font-size: 0.875rem;
}

.spinner {
  width: 28px;
  height: 28px;
  border: 2px solid var(--border-subtle, #22222e);
  border-top-color: var(--primary, #7c3aed);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 0.5rem;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
