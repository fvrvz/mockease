<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { applicationService } from '@/services/applications'
import { controllerService } from '@/services/controllers'
import { endpointService } from '@/services/endpoints'
import type { Application } from '@/types/application'
import type { Controller } from '@/types/controller'
import type { ApiEndpoint, HttpMethod, AuthInherit } from '@/types/endpoint'

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

// Testing UI state
const testTab = ref<'editor' | 'test' | 'curl'>('editor')
const testResponse = ref<{ status: number; timeMs: number; data: any; headers: any } | null>(null)
const isTesting = ref(false)

// JSON Editor State & Real-time Validation
const bodyText = ref('')
const jsonError = ref<string | null>(null)

function validateBodyText(text: string) {
  if (!text.trim()) {
    jsonError.value = null
    return
  }
  // Mask {{...}} placeholders with valid JSON string values so mock macros don't cause false positives
  const masked = text.replace(/\{\{[^{}]+\}\}/g, '"__MACRO__"')
  try {
    JSON.parse(masked)
    jsonError.value = null
  } catch (err: any) {
    jsonError.value = err.message || 'Invalid JSON syntax'
  }
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
  // Reposition caret
  setTimeout(() => {
    textarea.selectionStart = textarea.selectionEnd = start + 2
  }, 0)
  validateBodyText(bodyText.value)
}

function beautifyJson() {
  if (!bodyText.value.trim()) return
  try {
    // If it's standard JSON without macros
    const parsed = JSON.parse(bodyText.value)
    bodyText.value = JSON.stringify(parsed, null, 2)
    jsonError.value = null
    return
  } catch {
    // If it has macros, replace macros with placeholders, format, then restore
    const macroRegex = /\{\{[^{}]+\}\}/g
    const macros: string[] = []
    const placeholderPattern = (idx: number) => `"___MACRO_HOLDER_${idx}___"`
    
    const temp = bodyText.value.replace(macroRegex, (match) => {
      macros.push(match)
      return placeholderPattern(macros.length - 1)
    })
    
    try {
      let formatted = JSON.stringify(JSON.parse(temp), null, 2)
      macros.forEach((macro, idx) => {
        formatted = formatted.replace(placeholderPattern(idx), macro)
      })
      bodyText.value = formatted
      jsonError.value = null
    } catch (err: any) {
      jsonError.value = err.message || 'Cannot beautify invalid JSON'
    }
  }
}

function insertMacro(macro: string) {
  bodyText.value += (bodyText.value.length ? ' ' : '') + macro
  validateBodyText(bodyText.value)
}

const methodColors: Record<HttpMethod, string> = {
  GET: '#34d399',
  POST: '#60a5fa',
  PUT: '#fbbf24',
  PATCH: '#a78bfa',
  DELETE: '#f87171',
  HEAD: '#9ca3af',
  OPTIONS: '#9ca3af',
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
  testResponse.value = null
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
}

async function handleCreateEndpoint() {
  if (!selectedController.value || !newEpName.value.trim() || !newEpPath.value.trim()) return

  let parsedBody = null
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
    response_body: parsedBody,
  })

  endpoints.value.push(created)
  newEpName.value = ''
  newEpPath.value = ''
  showCreateEndpoint.value = false
  selectEndpoint(created)
}

async function toggleEndpoint(ep: ApiEndpoint, e: Event) {
  e.stopPropagation()
  const updated = await endpointService.toggle(ep.id)
  ep.is_enabled = updated.is_enabled
}

async function saveSelectedEndpoint() {
  if (!selectedEndpoint.value) return
  let bodyData: any = bodyText.value
  try {
    bodyData = JSON.parse(bodyText.value)
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
  alert('Endpoint saved successfully!')
}

const mockUrl = computed(() => {
  if (!app.value || !selectedEndpoint.value) return ''
  const origin = window.location.origin
  const path = selectedEndpoint.value.path.startsWith('/')
    ? selectedEndpoint.value.path.slice(1)
    : selectedEndpoint.value.path
  return `${origin}/mock/${app.value.slug}/${path}`
})

const generatedCurl = computed(() => {
  if (!selectedEndpoint.value) return ''
  let cmd = `curl -X ${selectedEndpoint.value.method} '${mockUrl.value}'`
  if (['POST', 'PUT', 'PATCH'].includes(selectedEndpoint.value.method)) {
    cmd += ` \\\n  -H 'Content-Type: application/json' \\\n  -d '{}'`
  }
  return cmd
})

async function copyToClipboard(text: string) {
  await navigator.clipboard.writeText(text)
  alert('Copied to clipboard!')
}

async function executeTestRequest() {
  if (!mockUrl.value || !selectedEndpoint.value) return
  isTesting.value = true
  testResponse.value = null

  const start = performance.now()
  try {
    const res = await fetch(mockUrl.value, {
      method: selectedEndpoint.value.method,
    })
    const timeMs = Math.round(performance.now() - start)
    const headersObj: Record<string, string> = {}
    res.headers.forEach((v, k) => {
      headersObj[k] = v
    })

    let data: any
    const contentType = res.headers.get('content-type') || ''
    if (contentType.includes('application/json')) {
      data = await res.json()
    } else {
      data = await res.text()
    }

    testResponse.value = {
      status: res.status,
      timeMs,
      data,
      headers: headersObj,
    }
  } catch (err: any) {
    testResponse.value = {
      status: 0,
      timeMs: Math.round(performance.now() - start),
      data: { error: err.message || 'Network request failed' },
      headers: {},
    }
  } finally {
    isTesting.value = false
  }
}
</script>

<template>
  <div v-if="loading" class="loading-state">Loading workspace...</div>
  <div v-else-if="app" class="workspace">
    <!-- Workspace Top Bar -->
    <div class="workspace__topbar">
      <div class="topbar-left">
        <RouterLink to="/" class="back-link">← Applications</RouterLink>
        <h1 class="workspace-title">{{ app.name }}</h1>
        <span class="base-badge">/mock/{{ app.slug }}</span>
      </div>
      <div class="topbar-right">
        <button
          class="btn btn--outline"
          @click="router.push({ name: 'application-settings', params: { id: app.id } })"
        >
          ⚙ Settings
        </button>
      </div>
    </div>

    <!-- Workspace Main Layout -->
    <div class="workspace__grid">
      <!-- Controllers Sidebar Column -->
      <aside class="sidebar-col">
        <div class="col-header">
          <span class="col-title">Controllers</span>
          <button class="btn btn--sm btn--primary" @click="showCreateCtrl = true">+</button>
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
            + New API
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
            @change="toggleEndpoint(ep, $event)"
          />
        </div>
      </section>

      <!-- Detail / Editor Column -->
      <main class="editor-col">
        <div v-if="!selectedEndpoint" class="no-selection">
          Select or create an endpoint to view details and configure responses.
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
              <button class="btn btn--sm btn--outline" @click="copyToClipboard(mockUrl)">
                Copy URL
              </button>
              <button class="btn btn--sm btn--outline" @click="copyToClipboard(generatedCurl)">
                Copy cURL
              </button>
              <button class="btn btn--sm btn--primary" @click="saveSelectedEndpoint">
                Save
              </button>
            </div>
          </div>

          <!-- URL Display Banner -->
          <div class="mock-url-box">
            <span class="mock-url-label">Mock URL:</span>
            <code class="mock-url-code">{{ mockUrl }}</code>
          </div>

          <!-- View Tabs (Editor / Tester / cURL) -->
          <div class="tab-bar">
            <button
              class="tab-btn"
              :class="{ 'tab-btn--active': testTab === 'editor' }"
              @click="testTab = 'editor'"
            >
              Response Configuration
            </button>
            <button
              class="tab-btn"
              :class="{ 'tab-btn--active': testTab === 'test' }"
              @click="testTab = 'test'"
            >
              Test API
            </button>
            <button
              class="tab-btn"
              :class="{ 'tab-btn--active': testTab === 'curl' }"
              @click="testTab = 'curl'"
            >
              cURL Example
            </button>
          </div>

          <!-- Configuration Tab -->
          <div v-if="testTab === 'editor'" class="tab-content">
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
                  ✨ Beautify JSON
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
                <span class="error-icon">⚠️</span>
                <span class="error-text">JSON Syntax Error: {{ jsonError }}</span>
              </div>
            </div>
          </div>

          <!-- Test API Tab -->
          <div v-if="testTab === 'test'" class="tab-content">
            <div class="test-controls">
              <button
                class="btn btn--primary"
                :disabled="isTesting"
                @click="executeTestRequest"
              >
                {{ isTesting ? 'Sending Request...' : 'Send Mock Request' }}
              </button>
            </div>

            <div v-if="testResponse" class="test-result">
              <div class="result-stats">
                <span class="res-status" :class="testResponse.status < 400 ? 'status--ok' : 'status--err'">
                  Status: {{ testResponse.status }}
                </span>
                <span class="res-time">Latency: {{ testResponse.timeMs }} ms</span>
              </div>
              <div class="result-body">
                <pre class="code-pre">{{ JSON.stringify(testResponse.data, null, 2) }}</pre>
              </div>
            </div>
          </div>

          <!-- cURL Tab -->
          <div v-if="testTab === 'curl'" class="tab-content">
            <div class="curl-box">
              <pre class="code-pre">{{ generatedCurl }}</pre>
            </div>
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
  </div>
</template>

<style scoped>
.workspace {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 56px);
  background: #0f0f11;
  color: #f1f1f8;
}

.workspace__topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1.5rem;
  background: #141418;
  border-bottom: 1px solid #2a2a35;
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.back-link {
  color: #71718a;
  text-decoration: none;
  font-size: 0.875rem;
}
.back-link:hover {
  color: #f1f1f8;
}

.workspace-title {
  font-size: 1.25rem;
  font-weight: 700;
  margin: 0;
}

.base-badge {
  font-family: monospace;
  font-size: 0.8125rem;
  background: #1f1f27;
  color: #a78bfa;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
}

.workspace__grid {
  display: grid;
  grid-template-columns: 240px 300px 1fr;
  flex: 1;
  overflow: hidden;
}

.sidebar-col, .endpoints-col {
  background: #141418;
  border-right: 1px solid #2a2a35;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.col-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.875rem 1rem;
  border-bottom: 1px solid #2a2a35;
}

.col-title {
  font-size: 0.8125rem;
  font-weight: 600;
  text-transform: uppercase;
  color: #71718a;
  letter-spacing: 0.05em;
}

.ctrl-item, .ep-item {
  display: flex;
  align-items: center;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #1f1f27;
  cursor: pointer;
  transition: background 0.15s;
}

.ctrl-item:hover, .ep-item:hover {
  background: #1b1b22;
}

.ctrl-item--active, .ep-item--active {
  background: #252533;
  border-left: 3px solid #7c3aed;
}

.ctrl-item__name {
  flex: 1;
  font-size: 0.9375rem;
  font-weight: 500;
}

.ctrl-item__count {
  font-size: 0.75rem;
  background: #2a2a35;
  padding: 0.15rem 0.4rem;
  border-radius: 999px;
  color: #9999b3;
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

.editor-col {
  background: #0f0f11;
  padding: 1.5rem;
  overflow-y: auto;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
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

.mock-url-box {
  background: #18181c;
  border: 1px solid #2a2a35;
  border-radius: 8px;
  padding: 0.625rem 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.mock-url-label {
  font-size: 0.8125rem;
  color: #71718a;
}

.mock-url-code {
  color: #34d399;
  font-family: monospace;
  font-size: 0.875rem;
}

.tab-bar {
  display: flex;
  border-bottom: 1px solid #2a2a35;
  margin-bottom: 1.5rem;
}

.tab-btn {
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  color: #71718a;
  padding: 0.625rem 1.25rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
}

.tab-btn--active {
  color: #a78bfa;
  border-bottom-color: #7c3aed;
}

.code-area, .code-pre {
  font-family: monospace;
  font-size: 0.875rem;
  line-height: 1.4;
}

.code-pre {
  background: #18181c;
  border: 1px solid #2a2a35;
  border-radius: 8px;
  padding: 1rem;
  overflow-x: auto;
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
  background: #1f1f27;
  color: #a78bfa;
  font-family: monospace;
  font-size: 0.6875rem;
  padding: 0.15rem 0.45rem;
  border-radius: 4px;
  border: 1px solid #3b3b4f;
  cursor: pointer;
  user-select: none;
  transition: all 0.15s;
}

.macro-tag:hover {
  background: #2b2b38;
  color: #c4b5fd;
  border-color: #7c3aed;
}

.beautify-btn {
  font-size: 0.75rem;
  white-space: nowrap;
}

.code-area--error {
  border-color: #ef4444 !important;
  box-shadow: 0 0 0 1px rgba(239, 68, 68, 0.2);
}

.json-error-banner {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 6px;
}

.error-icon {
  font-size: 0.875rem;
}

.error-text {
  color: #f87171;
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

.form-select:focus {
  border-color: #7c3aed;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%23a78bfa' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
}

.result-stats {
  display: flex;
  gap: 1rem;
  margin-bottom: 0.75rem;
}

.status--ok { color: #34d399; font-weight: 600; }
.status--err { color: #f87171; font-weight: 600; }
.res-time { color: #71718a; font-size: 0.875rem; }

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

.modal__footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1.5rem;
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

.btn--ghost {
  background: transparent;
  color: #9999b3;
}

.col-empty, .no-selection, .loading-state {
  padding: 2rem 1rem;
  text-align: center;
  color: #71718a;
  font-size: 0.875rem;
}
</style>
