import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useApplicationStore } from '@/stores/applications'
import { applicationService } from '@/services/applications'
import type { Application } from '@/types/application'

vi.mock('@/services/applications', () => ({
  applicationService: {
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    toggle: vi.fn(),
  },
}))

describe('Application Store', () => {
  const dummyApp: Application = {
    id: 'app-1',
    user_id: 'user-1',
    name: 'Test App',
    slug: 'test-app',
    description: 'A mock application',
    is_enabled: true,
    created_at: '2026-10-08T00:00:00Z',
    updated_at: '2026-10-08T00:00:00Z',
  }

  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('fetches applications list', async () => {
    vi.mocked(applicationService.list).mockResolvedValueOnce([dummyApp])
    const store = useApplicationStore()

    await store.fetchApplications()
    expect(store.applications).toHaveLength(1)
    expect(store.applications[0]!.name).toBe('Test App')
    expect(store.activeApps).toHaveLength(1)
  })

  it('creates application and prepends it to state', async () => {
    vi.mocked(applicationService.create).mockResolvedValueOnce(dummyApp)
    const store = useApplicationStore()

    const created = await store.createApplication({ name: 'Test App' })
    expect(created.id).toBe('app-1')
    expect(store.applications).toContainEqual(dummyApp)
  })

  it('toggles application status', async () => {
    const store = useApplicationStore()
    store.applications = [{ ...dummyApp, is_enabled: true }]
    store.currentApp = { ...dummyApp, is_enabled: true }

    vi.mocked(applicationService.toggle).mockResolvedValueOnce({
      ...dummyApp,
      is_enabled: false,
    })

    await store.toggleApplication('app-1')
    expect(store.applications[0]!.is_enabled).toBe(false)
    expect(store.currentApp?.is_enabled).toBe(false)
  })

  it('deletes application and removes it from state', async () => {
    const store = useApplicationStore()
    store.applications = [dummyApp]

    vi.mocked(applicationService.delete).mockResolvedValueOnce()
    await store.deleteApplication('app-1')

    expect(store.applications).toHaveLength(0)
  })
})
