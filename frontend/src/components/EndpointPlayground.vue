<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import {
  Zap,
  Code2,
  Send,
  Plus,
  Trash2,
  Sparkles,
  Clock,
  HardDrive,
  Copy,
  Check,
  AlertCircle,
  Rocket,
} from '@lucide/vue'
import { formatJsonWithMacros, validateJsonWithMacros } from '@/utils/jsonMacroHelper'
import type { ApiEndpoint, HttpMethod } from '@/types/endpoint'

interface KeyValuePair {
  id: string
  key: string
  value: string
  enabled: boolean
}

const props = defineProps<{
  endpoint: ApiEndpoint
  appSlug: string
}>()

const activeSubTab = ref<'tester' | 'snippets'>('tester')
const snippetLanguage = ref<'curl' | 'fetch' | 'axios' | 'python'>('curl')

// Request configuration state
const pathVariables = ref<Record<string, string>>({})
const queryParams = ref<KeyValuePair[]>([])
const requestHeaders = ref<KeyValuePair[]>([])
const requestBody = ref('')
const requestBodyError = ref<string | null>(null)

// Testing & response state
const isSending = ref(false)
const responseData = ref<{
  status: number
  statusText: string
  timeMs: number
  sizeBytes: number
  headers: Record<string, string>
  body: unknown
  isJson: boolean
} | null>(null)
const responseViewTab = ref<'body' | 'headers'>('body')
const copyFeedback = ref<string | null>(null)

// Extract path variables from endpoint path e.g. /users/{id}/{role}
const extractedParamNames = computed(() => {
  const matches = props.endpoint.path.match(/\{([a-zA-Z0-9_-]+)\}/g)
  if (!matches) return []
  return matches.map((m) => m.slice(1, -1))
})

// Initialize / reset state when endpoint changes
watch(
  () => props.endpoint,
  (ep) => {
    const vars: Record<string, string> = {}
    for (const name of extractedParamNames.value) {
      vars[name] = ''
    }
    pathVariables.value = vars

    queryParams.value = []
    if (ep.request_params) {
      for (const p of ep.request_params) {
        if (p.param_type === 'query') {
          queryParams.value.push({
            id: Math.random().toString(36).substring(2, 9),
            key: p.name,
            value: p.default_val ?? '',
            enabled: true,
          })
        }
      }
    }

    requestHeaders.value = [
      {
        id: 'h-accept',
        key: 'Accept',
        value: 'application/json',
        enabled: true,
      },
    ]

    if (['POST', 'PUT', 'PATCH'].includes(ep.method)) {
      requestHeaders.value.push({
        id: 'h-content-type',
        key: 'Content-Type',
        value: 'application/json',
        enabled: true,
      })
      requestBody.value = '{\n  "example": "data"\n}'
    } else {
      requestBody.value = ''
    }

    requestBodyError.value = null
    responseData.value = null
  },
  { immediate: true },
)

function addQueryParam() {
  queryParams.value.push({
    id: Math.random().toString(36).substring(2, 9),
    key: '',
    value: '',
    enabled: true,
  })
}

function removeQueryParam(index: number) {
  queryParams.value.splice(index, 1)
}

function addHeader() {
  requestHeaders.value.push({
    id: Math.random().toString(36).substring(2, 9),
    key: '',
    value: '',
    enabled: true,
  })
}

function removeHeader(index: number) {
  requestHeaders.value.splice(index, 1)
}

function formatRequestBody() {
  if (!requestBody.value.trim()) return
  const res = formatJsonWithMacros(requestBody.value)
  if (res.error) {
    requestBodyError.value = res.error
  } else {
    requestBody.value = res.formatted
    requestBodyError.value = null
  }
}

// Compute effective resolved URL
const resolvedRelativePath = computed(() => {
  let resolved = props.endpoint.path
  for (const [key, val] of Object.entries(pathVariables.value)) {
    const placeholder = `{${key}}`
    resolved = resolved.replace(placeholder, val ? encodeURIComponent(val) : placeholder)
  }
  return resolved.startsWith('/') ? resolved.slice(1) : resolved
})

const queryString = computed(() => {
  const activeParams = queryParams.value.filter((p) => p.enabled && p.key.trim().length > 0)
  if (activeParams.length === 0) return ''
  const searchParams = new URLSearchParams()
  for (const p of activeParams) {
    searchParams.append(p.key.trim(), p.value)
  }
  return `?${searchParams.toString()}`
})

const effectiveUrl = computed(() => {
  const origin = window.location.origin
  return `${origin}/mock/${props.appSlug}/${resolvedRelativePath.value}${queryString.value}`
})

// Send test request
async function executeRequest() {
  if (isSending.value) return
  isSending.value = true
  responseData.value = null

  // Validate body if present with macros support
  if (['POST', 'PUT', 'PATCH'].includes(props.endpoint.method) && requestBody.value.trim()) {
    const err = validateJsonWithMacros(requestBody.value)
    if (err) {
      requestBodyError.value = err
      isSending.value = false
      return
    }
    requestBodyError.value = null
  }

  const headersObj: Record<string, string> = {}
  for (const h of requestHeaders.value) {
    if (h.enabled && h.key.trim()) {
      headersObj[h.key.trim()] = h.value
    }
  }

  const start = performance.now()
  try {
    const options: RequestInit = {
      method: props.endpoint.method,
      headers: headersObj,
    }

    if (['POST', 'PUT', 'PATCH'].includes(props.endpoint.method) && requestBody.value.trim()) {
      options.body = requestBody.value
    }

    const res = await fetch(effectiveUrl.value, options)
    const timeMs = Math.round(performance.now() - start)

    const resHeaders: Record<string, string> = {}
    res.headers.forEach((v, k) => {
      resHeaders[k] = v
    })

    const rawText = await res.text()
    const sizeBytes = new Blob([rawText]).size
    let parsedBody: unknown = rawText
    let isJson = false

    try {
      parsedBody = JSON.parse(rawText)
      isJson = true
    } catch {
      // Keep as raw text
    }

    responseData.value = {
      status: res.status,
      statusText: res.statusText || (res.status === 200 ? 'OK' : 'Response'),
      timeMs,
      sizeBytes,
      headers: resHeaders,
      body: parsedBody,
      isJson,
    }
  } catch (err: unknown) {
    const timeMs = Math.round(performance.now() - start)
    const errorMsg = err instanceof Error ? err.message : 'Network connection failed'
    responseData.value = {
      status: 0,
      statusText: 'Network Error',
      timeMs,
      sizeBytes: 0,
      headers: {},
      body: { error: errorMsg },
      isJson: true,
    }
  } finally {
    isSending.value = false
  }
}

// Code Snippet Generators
const generatedSnippets = computed(() => {
  const url = effectiveUrl.value
  const method = props.endpoint.method
  const activeHeaders = requestHeaders.value.filter((h) => h.enabled && h.key.trim().length > 0)
  const hasBody = ['POST', 'PUT', 'PATCH'].includes(method) && requestBody.value.trim().length > 0

  // 1. cURL
  let curl = `curl -X ${method} "${url}"`
  for (const h of activeHeaders) {
    curl += ` \\\n  -H "${h.key.trim()}: ${h.value}"`
  }
  if (hasBody) {
    const escaped = requestBody.value.replace(/'/g, "'\\''")
    curl += ` \\\n  -d '${escaped}'`
  }

  // 2. JavaScript Fetch
  const fetchHeaders: Record<string, string> = {}
  activeHeaders.forEach((h) => {
    fetchHeaders[h.key.trim()] = h.value
  })

  let fetchSnippet = `const response = await fetch("${url}", {\n  method: "${method}",\n`
  if (Object.keys(fetchHeaders).length > 0) {
    fetchSnippet += `  headers: ${JSON.stringify(fetchHeaders, null, 4).replace(/\n/g, '\n  ')},\n`
  }
  if (hasBody) {
    fetchSnippet += `  body: JSON.stringify(${requestBody.value.replace(/\n/g, '\n  ')}),\n`
  }
  fetchSnippet += `});\n\nconst data = await response.json();\nconsole.log(data);`

  // 3. Axios
  let axiosSnippet = `import axios from 'axios';\n\n`
  const axiosConfig: Record<string, unknown> = {}
  if (Object.keys(fetchHeaders).length > 0) {
    axiosConfig.headers = fetchHeaders
  }

  if (hasBody) {
    axiosSnippet += `const data = ${requestBody.value};\n\n`
    axiosSnippet += `const response = await axios.${method.toLowerCase()}("${url}", data`
    if (Object.keys(axiosConfig).length > 0) {
      axiosSnippet += `, ${JSON.stringify(axiosConfig, null, 2)}`
    }
    axiosSnippet += `);\n\nconsole.log(response.data);`
  } else {
    axiosSnippet += `const response = await axios.${method.toLowerCase()}("${url}"`
    if (Object.keys(axiosConfig).length > 0) {
      axiosSnippet += `, ${JSON.stringify(axiosConfig, null, 2)}`
    }
    axiosSnippet += `);\n\nconsole.log(response.data);`
  }

  // 4. Python
  let pySnippet = `import requests\n\n`
  pySnippet += `url = "${url}"\n`
  if (Object.keys(fetchHeaders).length > 0) {
    pySnippet += `headers = ${JSON.stringify(fetchHeaders, null, 4)}\n`
  }
  if (hasBody) {
    pySnippet += `payload = ${requestBody.value}\n\n`
    pySnippet += `response = requests.${method.toLowerCase()}(\n    url,\n`
    if (Object.keys(fetchHeaders).length > 0) pySnippet += `    headers=headers,\n`
    pySnippet += `    json=payload\n)\n`
  } else {
    pySnippet += `\nresponse = requests.${method.toLowerCase()}(url`
    if (Object.keys(fetchHeaders).length > 0) pySnippet += `, headers=headers`
    pySnippet += `)\n`
  }
  pySnippet += `\nprint(response.status_code)\nprint(response.json())`

  return {
    curl,
    fetch: fetchSnippet,
    axios: axiosSnippet,
    python: pySnippet,
  }
})

async function copyCode(text: string) {
  try {
    await navigator.clipboard.writeText(text)
    copyFeedback.value = 'Copied to clipboard!'
  } catch {
    copyFeedback.value = 'Failed to copy'
  }
  setTimeout(() => {
    copyFeedback.value = null
  }, 2000)
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

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}
</script>

<template>
  <div class="playground">
    <!-- Sub-tab Navigation (Tester vs Code Snippets) -->
    <div class="playground-nav">
      <div class="nav-left">
        <button
          type="button"
          class="nav-tab"
          :class="{ 'nav-tab--active': activeSubTab === 'tester' }"
          @click="activeSubTab = 'tester'"
        >
          <Zap :size="14" class="tab-icon" />
          <span>Live Request Runner</span>
        </button>
        <button
          type="button"
          class="nav-tab"
          :class="{ 'nav-tab--active': activeSubTab === 'snippets' }"
          @click="activeSubTab = 'snippets'"
        >
          <Code2 :size="14" class="tab-icon" />
          <span>1-Click Code Snippets</span>
        </button>
      </div>

      <div v-if="copyFeedback" class="copy-alert">
        <Check :size="13" class="alert-icon" />
        <span>{{ copyFeedback }}</span>
      </div>
    </div>

    <!-- ──────────────────────── 1. Live Tester ──────────────────────── -->
    <div v-if="activeSubTab === 'tester'" class="tester-container">
      <!-- Request Bar -->
      <div class="request-bar">
        <span
          class="method-badge"
          :style="{ color: methodColors[endpoint.method] }"
        >
          {{ endpoint.method }}
        </span>
        <input
          :value="effectiveUrl"
          type="text"
          readonly
          class="url-input"
          title="Effective Mock Request URL"
        />
        <button
          type="button"
          class="btn btn--primary btn-send"
          :disabled="isSending"
          @click="executeRequest"
        >
          <Send :size="13" class="btn-icon" />
          <span>{{ isSending ? 'Sending…' : 'Send Request' }}</span>
        </button>
      </div>

      <!-- Path Variables Section (if endpoint path contains placeholders) -->
      <div v-if="extractedParamNames.length > 0" class="param-box">
        <div class="param-box__header">
          <span class="box-title">Path Variables</span>
          <span class="box-desc">Substitutes <code>{variable}</code> segments in URL</span>
        </div>
        <div class="vars-grid">
          <div
            v-for="name in extractedParamNames"
            :key="name"
            class="var-row"
          >
            <label class="var-label">{{ name }}</label>
            <input
              v-model="pathVariables[name]"
              type="text"
              class="form-input var-input"
              placeholder="e.g. 123"
            />
          </div>
        </div>
      </div>

      <!-- Query Parameters Section -->
      <div class="param-box">
        <div class="param-box__header">
          <span class="box-title">Query Parameters</span>
          <button type="button" class="btn btn--ghost btn--xs" @click="addQueryParam">
            <Plus :size="12" class="btn-icon" />
            <span>Add Query Param</span>
          </button>
        </div>

        <div v-if="queryParams.length === 0" class="empty-hint">
          No query parameters set. Click above to add query parameters.
        </div>

        <div v-else class="kv-list">
          <div v-for="(p, idx) in queryParams" :key="p.id" class="kv-row">
            <input v-model="p.enabled" type="checkbox" class="kv-check" title="Toggle param" />
            <input
              v-model="p.key"
              type="text"
              class="form-input kv-key"
              placeholder="Parameter name"
            />
            <input
              v-model="p.value"
              type="text"
              class="form-input kv-val"
              placeholder="Value"
            />
            <button
              type="button"
              class="btn-del"
              title="Remove parameter"
              @click="removeQueryParam(idx)"
            >
              <Trash2 :size="14" />
            </button>
          </div>
        </div>
      </div>

      <!-- Request Headers Section -->
      <div class="param-box">
        <div class="param-box__header">
          <span class="box-title">Request Headers</span>
          <button type="button" class="btn btn--ghost btn--xs" @click="addHeader">
            <Plus :size="12" class="btn-icon" />
            <span>Add Header</span>
          </button>
        </div>

        <div class="kv-list">
          <div v-for="(h, idx) in requestHeaders" :key="h.id" class="kv-row">
            <input v-model="h.enabled" type="checkbox" class="kv-check" title="Toggle header" />
            <input
              v-model="h.key"
              type="text"
              class="form-input kv-key"
              placeholder="Header name"
            />
            <input
              v-model="h.value"
              type="text"
              class="form-input kv-val"
              placeholder="Header value"
            />
            <button
              type="button"
              class="btn-del"
              title="Remove header"
              @click="removeHeader(idx)"
            >
              <Trash2 :size="14" />
            </button>
          </div>
        </div>
      </div>

      <!-- Request Body Section (for POST, PUT, PATCH) -->
      <div v-if="['POST', 'PUT', 'PATCH'].includes(endpoint.method)" class="param-box">
        <div class="param-box__header">
          <span class="box-title">Request Body (JSON)</span>
          <button
            type="button"
            class="btn btn--ghost btn--xs"
            @click="formatRequestBody"
          >
            <Sparkles :size="12" class="btn-icon" />
            <span>Format JSON</span>
          </button>
        </div>

        <textarea
          v-model="requestBody"
          class="form-textarea body-area"
          rows="6"
          spellcheck="false"
          placeholder='{\n  "key": "value"\n}'
        ></textarea>

        <div v-if="requestBodyError" class="error-banner">
          <AlertCircle :size="14" class="alert-icon" />
          <span>{{ requestBodyError }}</span>
        </div>
      </div>

      <!-- Response Inspector -->
      <div class="response-card">
        <div class="response-header">
          <div class="res-meta">
            <span class="res-title">Live Mock Response</span>
            <template v-if="responseData">
              <span
                class="status-pill"
                :class="{
                  'status--success': responseData.status >= 200 && responseData.status < 300,
                  'status--warn': responseData.status >= 300 && responseData.status < 400,
                  'status--error': responseData.status >= 400 || responseData.status === 0,
                }"
              >
                {{ responseData.status }} {{ responseData.statusText }}
              </span>
              <span class="meta-pill">
                <Clock :size="12" class="meta-icon" />
                <span>{{ responseData.timeMs }} ms</span>
              </span>
              <span class="meta-pill">
                <HardDrive :size="12" class="meta-icon" />
                <span>{{ formatBytes(responseData.sizeBytes) }}</span>
              </span>
            </template>
          </div>

          <div v-if="responseData" class="res-actions">
            <div class="res-tabs">
              <button
                type="button"
                class="res-tab"
                :class="{ 'res-tab--active': responseViewTab === 'body' }"
                @click="responseViewTab = 'body'"
              >
                Body
              </button>
              <button
                type="button"
                class="res-tab"
                :class="{ 'res-tab--active': responseViewTab === 'headers' }"
                @click="responseViewTab = 'headers'"
              >
                Headers ({{ Object.keys(responseData.headers).length }})
              </button>
            </div>
            <button
              type="button"
              class="btn btn--outline btn--xs"
              @click="copyCode(JSON.stringify(responseData.body, null, 2))"
            >
              <Copy :size="12" class="btn-icon" />
              <span>Copy Body</span>
            </button>
          </div>
        </div>

        <!-- Waiting State -->
        <div v-if="!responseData && !isSending" class="res-placeholder">
          <Rocket :size="28" class="placeholder-icon-svg" />
          <p class="placeholder-text">Click <strong>Send Request</strong> above to trigger this mock endpoint live.</p>
        </div>

        <!-- Loading State -->
        <div v-else-if="isSending" class="res-loading">
          <div class="spinner"></div>
          <span>Awaiting mock runtime response…</span>
        </div>

        <!-- Rendered Response Body -->
        <div v-else-if="responseData && responseViewTab === 'body'" class="res-content">
          <pre class="code-viewer">{{ typeof responseData.body === 'object' ? JSON.stringify(responseData.body, null, 2) : responseData.body }}</pre>
        </div>

        <!-- Rendered Response Headers -->
        <div v-else-if="responseData && responseViewTab === 'headers'" class="headers-table">
          <div v-if="Object.keys(responseData.headers).length === 0" class="empty-hint">
            No response headers returned.
          </div>
          <table v-else class="table">
            <thead>
              <tr>
                <th>Header</th>
                <th>Value</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(val, hdr) in responseData.headers" :key="hdr">
                <td class="hdr-key">{{ hdr }}</td>
                <td class="hdr-val">{{ val }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- ──────────────────────── 2. Code Snippets ──────────────────────── -->
    <div v-else class="snippets-container">
      <div class="snippet-nav">
        <div class="snippet-tabs">
          <button
            type="button"
            class="snip-tab"
            :class="{ 'snip-tab--active': snippetLanguage === 'curl' }"
            @click="snippetLanguage = 'curl'"
          >
            cURL (CLI)
          </button>
          <button
            type="button"
            class="snip-tab"
            :class="{ 'snip-tab--active': snippetLanguage === 'fetch' }"
            @click="snippetLanguage = 'fetch'"
          >
            JavaScript (Fetch)
          </button>
          <button
            type="button"
            class="snip-tab"
            :class="{ 'snip-tab--active': snippetLanguage === 'axios' }"
            @click="snippetLanguage = 'axios'"
          >
            Axios (TS/JS)
          </button>
          <button
            type="button"
            class="snip-tab"
            :class="{ 'snip-tab--active': snippetLanguage === 'python' }"
            @click="snippetLanguage = 'python'"
          >
            Python (Requests)
          </button>
        </div>

        <button
          type="button"
          class="btn btn--outline btn--sm btn-copy-snip"
          @click="copyCode(generatedSnippets[snippetLanguage])"
        >
          <Copy :size="13" class="btn-icon" />
          <span>Copy Code</span>
        </button>
      </div>

      <div class="snippet-code-box">
        <pre class="code-viewer">{{ generatedSnippets[snippetLanguage] }}</pre>
      </div>
    </div>
  </div>
</template>

<style scoped>
.playground {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  background: var(--bg-surface, #121217);
  border-radius: 12px;
  border: 1px solid var(--border-subtle, #22222e);
  padding: 1.25rem;
}

/* Nav */
.playground-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border-subtle, #22222e);
  padding-bottom: 0.75rem;
}

.nav-left {
  display: flex;
  gap: 0.5rem;
}

.nav-tab {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  background: transparent;
  border: 1px solid transparent;
  color: var(--text-muted, #9494a8);
  font-size: 0.875rem;
  font-weight: 600;
  padding: 0.45rem 0.85rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all var(--transition-fast, 0.15s);
}

.nav-tab:hover {
  color: var(--text-main, #f4f4f7);
  background: var(--bg-surface-elevated, #181820);
}

.nav-tab--active {
  background: var(--bg-surface-elevated, #181820);
  border-color: var(--border-subtle, #22222e);
  color: var(--primary, #7c3aed);
}

.tab-icon,
.btn-icon,
.meta-icon {
  flex-shrink: 0;
}

.copy-alert {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.8125rem;
  color: var(--success, #10b981);
  font-weight: 600;
  animation: fadeIn 0.2s ease-in;
}

.alert-icon {
  flex-shrink: 0;
}

/* Tester */
.tester-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.request-bar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: var(--bg-surface-elevated, #181820);
  padding: 0.5rem;
  border-radius: 8px;
  border: 1px solid var(--border-subtle, #22222e);
}

.method-badge {
  font-family: monospace;
  font-size: 0.875rem;
  font-weight: 700;
  padding: 0.25rem 0.6rem;
  background: var(--bg-surface, #121217);
  border-radius: 6px;
  border: 1px solid var(--border-subtle, #22222e);
}

.url-input {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--text-main, #f4f4f7);
  font-family: monospace;
  font-size: 0.875rem;
  outline: none;
}

.btn-send {
  white-space: nowrap;
}

/* Boxes */
.param-box {
  background: var(--bg-surface-elevated, #181820);
  border: 1px solid var(--border-subtle, #22222e);
  border-radius: 8px;
  padding: 0.875rem;
}

.param-box__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.625rem;
}

.box-title {
  font-size: 0.8125rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted, #9494a8);
}

.box-desc {
  font-size: 0.75rem;
  color: var(--text-dim, #606075);
}

.box-desc code {
  color: var(--primary, #7c3aed);
}

.vars-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 0.5rem;
}

.var-row {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.var-label {
  font-size: 0.75rem;
  font-family: monospace;
  color: var(--primary, #7c3aed);
  font-weight: 600;
}

.var-input {
  padding: 0.4rem 0.6rem;
  font-size: 0.8125rem;
}

/* KV list */
.kv-list {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.kv-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.kv-check {
  cursor: pointer;
  accent-color: var(--primary, #7c3aed);
}

.kv-key {
  flex: 1;
  padding: 0.35rem 0.6rem;
  font-size: 0.8125rem;
}

.kv-val {
  flex: 2;
  padding: 0.35rem 0.6rem;
  font-size: 0.8125rem;
}

.btn-del {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: var(--text-dim, #606075);
  cursor: pointer;
  padding: 0.35rem;
  border-radius: 4px;
  transition: all var(--transition-fast, 0.15s);
}

.btn-del:hover {
  color: var(--danger, #ef4444);
  background: var(--danger-bg, rgba(239, 68, 68, 0.1));
}

.empty-hint {
  font-size: 0.8125rem;
  color: var(--text-dim, #606075);
  font-style: italic;
  padding: 0.25rem 0;
}

.body-area {
  width: 100%;
  font-family: monospace;
  font-size: 0.8125rem;
}

.error-banner {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  margin-top: 0.5rem;
  font-size: 0.8125rem;
  color: var(--danger, #ef4444);
  background: var(--danger-bg, rgba(239, 68, 68, 0.1));
  border: 1px solid var(--danger-border, rgba(239, 68, 68, 0.25));
  padding: 0.4rem 0.6rem;
  border-radius: 6px;
}

/* Response */
.response-card {
  background: var(--bg-surface-elevated, #181820);
  border: 1px solid var(--border-subtle, #22222e);
  border-radius: 8px;
  overflow: hidden;
}

.response-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.625rem 0.875rem;
  background: var(--bg-surface, #121217);
  border-bottom: 1px solid var(--border-subtle, #22222e);
  flex-wrap: wrap;
  gap: 0.5rem;
}

.res-meta {
  display: flex;
  align-items: center;
  gap: 0.625rem;
}

.res-title {
  font-size: 0.8125rem;
  font-weight: 700;
  color: var(--text-main, #f4f4f7);
}

.status-pill {
  font-size: 0.75rem;
  font-weight: 700;
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
}

.status--success {
  background: var(--success-bg, rgba(16, 185, 129, 0.15));
  color: var(--success, #10b981);
  border: 1px solid var(--success-border, rgba(16, 185, 129, 0.3));
}

.status--warn {
  background: var(--warning-bg, rgba(245, 158, 11, 0.15));
  color: var(--warning, #f59e0b);
  border: 1px solid rgba(245, 158, 11, 0.3);
}

.status--error {
  background: var(--danger-bg, rgba(239, 68, 68, 0.15));
  color: var(--danger, #ef4444);
  border: 1px solid var(--danger-border, rgba(239, 68, 68, 0.3));
}

.meta-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.75rem;
  color: var(--text-muted, #9494a8);
}

.res-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.res-tabs {
  display: flex;
  gap: 0.25rem;
  background: var(--bg-surface-elevated, #181820);
  border-radius: 6px;
  padding: 0.15rem;
}

.res-tab {
  background: transparent;
  border: none;
  font-size: 0.75rem;
  color: var(--text-muted, #9494a8);
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  cursor: pointer;
}

.res-tab--active {
  background: var(--bg-surface, #121217);
  color: var(--text-main, #f4f4f7);
  font-weight: 600;
}

.res-placeholder,
.res-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2.5rem 1rem;
  text-align: center;
  gap: 0.5rem;
}

.placeholder-icon-svg {
  color: var(--text-muted, #9494a8);
  margin-bottom: 0.25rem;
}

.placeholder-text {
  font-size: 0.875rem;
  color: var(--text-muted, #9494a8);
}

.res-loading {
  color: var(--text-muted, #9494a8);
  font-size: 0.875rem;
}

.spinner {
  width: 24px;
  height: 24px;
  border: 2px solid var(--border-subtle, #22222e);
  border-top-color: var(--primary, #7c3aed);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.res-content {
  padding: 0.75rem;
  max-height: 380px;
  overflow: auto;
}

.code-viewer {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.8125rem;
  color: var(--text-main, #f4f4f7);
  line-height: 1.5;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
}

.headers-table {
  padding: 0.5rem;
  max-height: 300px;
  overflow: auto;
}

.table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8125rem;
}

.table th {
  text-align: left;
  padding: 0.4rem 0.6rem;
  color: var(--text-dim, #606075);
  font-weight: 600;
  border-bottom: 1px solid var(--border-subtle, #22222e);
}

.table td {
  padding: 0.4rem 0.6rem;
  border-bottom: 1px solid var(--border-subtle, #22222e);
}

.hdr-key {
  font-family: monospace;
  color: var(--primary, #7c3aed);
  width: 35%;
}

.hdr-val {
  font-family: monospace;
  color: var(--text-main, #f4f4f7);
  word-break: break-all;
}

/* Snippets */
.snippets-container {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.snippet-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.snippet-tabs {
  display: flex;
  gap: 0.35rem;
  background: var(--bg-surface-elevated, #181820);
  padding: 0.25rem;
  border-radius: 8px;
  border: 1px solid var(--border-subtle, #22222e);
}

.snip-tab {
  background: transparent;
  border: none;
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--text-muted, #9494a8);
  padding: 0.35rem 0.75rem;
  border-radius: 6px;
  cursor: pointer;
  transition: all var(--transition-fast, 0.15s);
}

.snip-tab:hover {
  color: var(--text-main, #f4f4f7);
}

.snip-tab--active {
  background: var(--bg-surface, #121217);
  color: var(--primary, #7c3aed);
  font-weight: 600;
}

.snippet-code-box {
  background: var(--bg-surface-elevated, #181820);
  border: 1px solid var(--border-subtle, #22222e);
  border-radius: 8px;
  padding: 1rem;
  max-height: 440px;
  overflow: auto;
}

/* Common form controls */
.form-input,
.form-textarea {
  background: var(--bg-surface, #121217);
  border: 1px solid var(--border-subtle, #22222e);
  border-radius: 6px;
  color: var(--text-main, #f4f4f7);
  font-size: 0.875rem;
  outline: none;
  transition: border-color var(--transition-fast, 0.15s);
}

.form-input:focus,
.form-textarea:focus {
  border-color: var(--border-focus, #8b5cf6);
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.375rem;
  padding: 0.4rem 0.85rem;
  border-radius: 6px;
  font-size: 0.8125rem;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all var(--transition-fast, 0.15s);
}

.btn--primary {
  background: var(--primary, #7c3aed);
  color: #fff;
}

.btn--primary:hover:not(:disabled) {
  background: var(--primary-hover, #6d28d9);
}

.btn--primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn--outline {
  background: transparent;
  color: var(--text-main, #f4f4f7);
  border: 1px solid var(--border-subtle, #22222e);
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

.btn--xs {
  font-size: 0.75rem;
  padding: 0.2rem 0.5rem;
}

.btn--sm {
  font-size: 0.8125rem;
  padding: 0.35rem 0.7rem;
}
</style>
