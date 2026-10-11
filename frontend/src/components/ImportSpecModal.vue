<script setup lang="ts">
import { ref, computed } from 'vue'
import { Upload, FileCode, Check, AlertCircle, X } from '@lucide/vue'

interface Props {
  show: boolean
  targetAppId?: string
  targetAppName?: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'imported', data: { spec: string; name?: string; targetAppId?: string }): void
}>()

const specContent = ref('')
const appName = ref('')
const fileName = ref<string | null>(null)
const error = ref<string | null>(null)
const isSubmitting = ref(false)
const isDragging = ref(false)

const detectedFormat = computed<'OpenAPI 3.x' | 'Swagger 2.0' | 'Postman v2.1' | 'Unknown' | null>(() => {
  const content = specContent.value.trim()
  if (!content) return null

  if (content.includes('"openapi"') || content.startsWith('openapi:') || content.includes('\nopenapi:')) {
    return 'OpenAPI 3.x'
  }
  if (content.includes('"swagger"') || content.startsWith('swagger:') || content.includes('\nswagger:')) {
    return 'Swagger 2.0'
  }
  if (content.includes('schema.getpostman.com') || content.includes('"_postman_id"')) {
    return 'Postman v2.1'
  }
  return 'Unknown'
})

function handleFileChange(e: Event) {
  const target = e.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    readFile(target.files[0]!)
  }
}

function handleDrop(e: DragEvent) {
  isDragging.value = false
  if (e.dataTransfer?.files && e.dataTransfer.files.length > 0) {
    readFile(e.dataTransfer.files[0]!)
  }
}

function readFile(file: File) {
  error.value = null
  fileName.value = file.name

  // Auto populate app name from file name if blank
  if (!appName.value && !props.targetAppId) {
    const baseName = file.name.replace(/\.[^/.]+$/, '').replace(/[-_]/g, ' ')
    appName.value = baseName.charAt(0).toUpperCase() + baseName.slice(1)
  }

  const reader = new FileReader()
  reader.onload = (event) => {
    const result = event.target?.result
    if (typeof result === 'string') {
      specContent.value = result
    }
  }
  reader.onerror = () => {
    error.value = 'Failed to read file'
  }
  reader.readAsText(file)
}

function resetForm() {
  specContent.value = ''
  appName.value = ''
  fileName.value = null
  error.value = null
  isSubmitting.value = false
}

function handleClose() {
  resetForm()
  emit('close')
}

async function handleSubmit() {
  if (!specContent.value.trim()) {
    error.value = 'Please provide an OpenAPI or Postman specification'
    return
  }

  error.value = null
  isSubmitting.value = true

  try {
    emit('imported', {
      spec: specContent.value.trim(),
      name: appName.value.trim() || undefined,
      targetAppId: props.targetAppId,
    })
  } catch (err: unknown) {
    const e = err as { message?: string }
    error.value = e.message ?? 'Import failed'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div v-if="show" class="modal-backdrop" @click="handleClose">
    <div class="modal-card" @click.stop>
      <div class="modal-header">
        <div>
          <h2 class="modal-title">
            {{ targetAppId ? 'Import into Application' : 'Import API Specification' }}
          </h2>
          <p class="modal-subtitle">
            <span v-if="targetAppName">
              Merge controllers and endpoints into <strong>{{ targetAppName }}</strong>.
            </span>
            <span v-else>
              Import OpenAPI 3.0, Swagger 2.0, or Postman v2.1 (JSON or YAML).
            </span>
          </p>
        </div>
        <button class="btn-close" @click="handleClose">
          <X :size="18" />
        </button>
      </div>

      <div class="modal-body">
        <!-- Error Alert -->
        <div v-if="error" class="alert-error">
          <AlertCircle :size="16" />
          <span>{{ error }}</span>
        </div>

        <!-- Optional Name field for new app -->
        <div v-if="!targetAppId" class="form-group">
          <label class="form-label">Application Name (Optional)</label>
          <input
            v-model="appName"
            type="text"
            class="form-input"
            placeholder="e.g. Petstore API (defaults to spec title)"
          />
        </div>

        <!-- File Upload Drop Zone -->
        <div
          class="dropzone"
          :class="{ 'dropzone--active': isDragging, 'dropzone--has-file': fileName }"
          @dragover.prevent="isDragging = true"
          @dragleave.prevent="isDragging = false"
          @drop.prevent="handleDrop"
        >
          <input
            id="specFileInput"
            type="file"
            accept=".json,.yaml,.yml,application/json,text/yaml"
            class="dropzone__input"
            @change="handleFileChange"
          />
          <label for="specFileInput" class="dropzone__label">
            <div class="dropzone__icon">
              <Upload v-if="!fileName" :size="24" />
              <FileCode v-else :size="24" />
            </div>
            <div class="dropzone__text">
              <span v-if="fileName" class="dropzone__filename">
                <Check :size="14" class="check-icon" /> {{ fileName }}
              </span>
              <span v-else>
                <strong>Click to browse</strong> or drag and drop spec file
              </span>
              <span class="dropzone__hint">Supports OpenAPI 3.x, Swagger 2.0, Postman v2.1 (.json, .yaml)</span>
            </div>
          </label>
        </div>

        <!-- Detected Format Badge -->
        <div v-if="detectedFormat" class="format-indicator">
          <span class="format-label">Detected Format:</span>
          <span
            class="format-badge"
            :class="{ 'format-badge--detected': detectedFormat !== 'Unknown' }"
          >
            {{ detectedFormat }}
          </span>
        </div>

        <!-- Raw Text Spec Area -->
        <div class="form-group">
          <label class="form-label">Or Paste Specification (JSON / YAML)</label>
          <textarea
            v-model="specContent"
            class="form-textarea"
            rows="7"
            placeholder="Paste raw OpenAPI 3.0 / Swagger JSON, YAML, or Postman Collection JSON here..."
          ></textarea>
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn btn--outline" :disabled="isSubmitting" @click="handleClose">
          Cancel
        </button>
        <button
          class="btn btn--primary"
          :disabled="isSubmitting || !specContent.trim()"
          @click="handleSubmit"
        >
          {{ isSubmitting ? 'Importing...' : 'Import Specification' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1.5rem;
}

.modal-card {
  width: 100%;
  max-width: 580px;
  background: var(--bg-card, #18181c);
  border: 1px solid var(--border-color, #2a2a35);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
  overflow: hidden;
}

.modal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--border-color, #2a2a35);
}

.modal-title {
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--text-color, #e8e8f0);
  margin: 0;
}

.modal-subtitle {
  font-size: 0.8125rem;
  color: #9999b3;
  margin: 0.25rem 0 0;
}

.btn-close {
  background: transparent;
  border: none;
  color: #9999b3;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}

.btn-close:hover {
  background: rgba(255, 255, 255, 0.05);
  color: #fff;
}

.modal-body {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  max-height: 70vh;
  overflow-y: auto;
}

.alert-error {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: rgba(239, 68, 68, 0.15);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 8px;
  color: #f87171;
  font-size: 0.875rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.form-label {
  font-size: 0.8125rem;
  font-weight: 600;
  color: #b3b3cc;
}

.form-input {
  padding: 0.625rem 0.875rem;
  background: #0f0f11;
  border: 1px solid var(--border-color, #2a2a35);
  border-radius: 8px;
  color: #e8e8f0;
  font-size: 0.875rem;
  outline: none;
  transition: border-color 0.15s;
}

.form-input:focus {
  border-color: var(--brand-color, #7c3aed);
}

.dropzone {
  border: 2px dashed #2a2a35;
  border-radius: 8px;
  padding: 1.25rem;
  background: rgba(255, 255, 255, 0.02);
  transition: all 0.2s;
  cursor: pointer;
}

.dropzone:hover,
.dropzone--active {
  border-color: var(--brand-color, #7c3aed);
  background: rgba(124, 58, 237, 0.05);
}

.dropzone--has-file {
  border-color: #10b981;
  background: rgba(16, 185, 129, 0.05);
}

.dropzone__input {
  display: none;
}

.dropzone__label {
  display: flex;
  align-items: center;
  gap: 1rem;
  cursor: pointer;
  width: 100%;
}

.dropzone__icon {
  width: 44px;
  height: 44px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.05);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #a78bfa;
}

.dropzone__text {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.875rem;
  color: #e8e8f0;
}

.dropzone__filename {
  font-weight: 600;
  color: #10b981;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.dropzone__hint {
  font-size: 0.75rem;
  color: #8888a0;
}

.format-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8125rem;
}

.format-label {
  color: #8888a0;
}

.format-badge {
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.08);
  color: #9999b3;
  font-size: 0.75rem;
  font-weight: 600;
}

.format-badge--detected {
  background: rgba(124, 58, 237, 0.15);
  color: #a78bfa;
  border: 1px solid rgba(124, 58, 237, 0.3);
}

.form-textarea {
  padding: 0.625rem 0.875rem;
  background: #0f0f11;
  border: 1px solid var(--border-color, #2a2a35);
  border-radius: 8px;
  color: #e8e8f0;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.8125rem;
  outline: none;
  resize: vertical;
}

.form-textarea:focus {
  border-color: var(--brand-color, #7c3aed);
}

.modal-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--border-color, #2a2a35);
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

.btn--outline {
  background: transparent;
  color: #9999b3;
  border: 1px solid var(--border-color, #2a2a35);
}

.btn--outline:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.05);
  color: #e8e8f0;
}

.btn--primary {
  background: var(--brand-color, #7c3aed);
  color: #fff;
}

.btn--primary:hover:not(:disabled) {
  opacity: 0.9;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
