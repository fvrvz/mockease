import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import type { Application, CreateApplicationRequest } from '@/types/application'
import { applicationService } from '@/services/applications'

export const useApplicationStore = defineStore('applications', () => {
  const applications = ref<Application[]>([])
  const currentApp = ref<Application | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const activeApps = computed(() => applications.value.filter((a) => a.is_enabled))

  async function fetchApplications() {
    loading.value = true
    error.value = null
    try {
      applications.value = await applicationService.list()
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } }
      error.value = e?.response?.data?.detail ?? 'Failed to load applications'
    } finally {
      loading.value = false
    }
  }

  async function fetchApplication(id: string) {
    loading.value = true
    try {
      currentApp.value = await applicationService.get(id)
    } finally {
      loading.value = false
    }
  }

  async function createApplication(data: CreateApplicationRequest) {
    loading.value = true
    try {
      const created = await applicationService.create(data)
      applications.value.unshift(created)
      return created
    } finally {
      loading.value = false
    }
  }

  async function toggleApplication(id: string) {
    const updated = await applicationService.toggle(id)
    const idx = applications.value.findIndex((a) => a.id === id)
    const appItem = applications.value[idx]
    if (appItem) {
      appItem.is_enabled = updated.is_enabled
    }
    if (currentApp.value?.id === id) {
      currentApp.value.is_enabled = updated.is_enabled
    }
  }

  async function deleteApplication(id: string) {
    await applicationService.delete(id)
    applications.value = applications.value.filter((a) => a.id !== id)
  }

  return {
    applications,
    currentApp,
    loading,
    error,
    activeApps,
    fetchApplications,
    fetchApplication,
    createApplication,
    toggleApplication,
    deleteApplication,
  }
})

