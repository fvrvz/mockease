import { describe, it, expect, beforeEach, vi } from 'vitest'
import api from '@/services/api'
import { authService } from '@/services/auth'
import { applicationService } from '@/services/applications'
import { controllerService } from '@/services/controllers'
import { endpointService } from '@/services/endpoints'

vi.mock('@/services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}))

describe('Services API Layer', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('authService', () => {
    it('register calls POST /auth/register', async () => {
      const mockUser = { id: '1', email: 'a@b.com', username: 'u', is_active: true }
      vi.mocked(api.post).mockResolvedValueOnce({ data: mockUser })

      const res = await authService.register({ email: 'a@b.com', username: 'u', password: 'p' })
      expect(api.post).toHaveBeenCalledWith('/auth/register', { email: 'a@b.com', username: 'u', password: 'p' })
      expect(res).toEqual(mockUser)
    })

    it('login calls POST /auth/login', async () => {
      const mockToken = { access_token: 't', token_type: 'bearer' }
      vi.mocked(api.post).mockResolvedValueOnce({ data: mockToken })

      const res = await authService.login({ email: 'a@b.com', password: 'p' })
      expect(api.post).toHaveBeenCalledWith('/auth/login', { email: 'a@b.com', password: 'p' })
      expect(res).toEqual(mockToken)
    })

    it('me calls GET /auth/me', async () => {
      const mockUser = { id: '1', email: 'a@b.com', username: 'u', is_active: true }
      vi.mocked(api.get).mockResolvedValueOnce({ data: mockUser })

      const res = await authService.me()
      expect(api.get).toHaveBeenCalledWith('/auth/me')
      expect(res).toEqual(mockUser)
    })
  })

  describe('applicationService', () => {
    it('calls list, get, create, update, delete, toggle', async () => {
      vi.mocked(api.get).mockResolvedValueOnce({ data: [] }).mockResolvedValueOnce({ data: { id: 'app-1' } })
      vi.mocked(api.post).mockResolvedValueOnce({ data: { id: 'app-1' } })
      vi.mocked(api.patch).mockResolvedValueOnce({ data: { id: 'app-1' } }).mockResolvedValueOnce({ data: { id: 'app-1', is_enabled: false } })
      vi.mocked(api.delete).mockResolvedValueOnce({})

      await applicationService.list()
      expect(api.get).toHaveBeenCalledWith('/applications')

      await applicationService.get('app-1')
      expect(api.get).toHaveBeenCalledWith('/applications/app-1')

      await applicationService.create({ name: 'App' })
      expect(api.post).toHaveBeenCalledWith('/applications', { name: 'App' })

      await applicationService.update('app-1', { name: 'App New' })
      expect(api.patch).toHaveBeenCalledWith('/applications/app-1', { name: 'App New' })

      await applicationService.toggle('app-1')
      expect(api.patch).toHaveBeenCalledWith('/applications/app-1/toggle')

      await applicationService.delete('app-1')
      expect(api.delete).toHaveBeenCalledWith('/applications/app-1')
    })
  })

  describe('controllerService', () => {
    it('calls list, get, create, update, delete, toggle', async () => {
      vi.mocked(api.get).mockResolvedValueOnce({ data: [] }).mockResolvedValueOnce({ data: { id: 'ctrl-1' } })
      vi.mocked(api.post).mockResolvedValueOnce({ data: { id: 'ctrl-1' } })
      vi.mocked(api.patch).mockResolvedValueOnce({ data: { id: 'ctrl-1' } }).mockResolvedValueOnce({ data: { id: 'ctrl-1', is_enabled: false } })
      vi.mocked(api.delete).mockResolvedValueOnce({})

      await controllerService.list('app-1')
      expect(api.get).toHaveBeenCalledWith('/applications/app-1/controllers')

      await controllerService.get('ctrl-1')
      expect(api.get).toHaveBeenCalledWith('/controllers/ctrl-1')

      await controllerService.create('app-1', { name: 'Ctrl' })
      expect(api.post).toHaveBeenCalledWith('/applications/app-1/controllers', { name: 'Ctrl' })

      await controllerService.update('ctrl-1', { name: 'Ctrl New' })
      expect(api.patch).toHaveBeenCalledWith('/controllers/ctrl-1', { name: 'Ctrl New' })

      await controllerService.toggle('ctrl-1')
      expect(api.patch).toHaveBeenCalledWith('/controllers/ctrl-1/toggle')

      await controllerService.delete('ctrl-1')
      expect(api.delete).toHaveBeenCalledWith('/controllers/ctrl-1')
    })
  })

  describe('endpointService', () => {
    it('calls list, get, create, update, delete, toggle', async () => {
      vi.mocked(api.get).mockResolvedValueOnce({ data: [] }).mockResolvedValueOnce({ data: { id: 'ep-1' } })
      vi.mocked(api.post).mockResolvedValueOnce({ data: { id: 'ep-1' } })
      vi.mocked(api.patch).mockResolvedValueOnce({ data: { id: 'ep-1' } }).mockResolvedValueOnce({ data: { id: 'ep-1', is_enabled: false } })
      vi.mocked(api.delete).mockResolvedValueOnce({})

      await endpointService.list('ctrl-1')
      expect(api.get).toHaveBeenCalledWith('/controllers/ctrl-1/endpoints')

      await endpointService.get('ep-1')
      expect(api.get).toHaveBeenCalledWith('/endpoints/ep-1')

      await endpointService.create('ctrl-1', { name: 'Ep', method: 'GET', path: '/test' })
      expect(api.post).toHaveBeenCalledWith('/controllers/ctrl-1/endpoints', { name: 'Ep', method: 'GET', path: '/test' })

      await endpointService.update('ep-1', { name: 'Ep New' })
      expect(api.patch).toHaveBeenCalledWith('/endpoints/ep-1', { name: 'Ep New' })

      await endpointService.toggle('ep-1')
      expect(api.patch).toHaveBeenCalledWith('/endpoints/ep-1/toggle')

      await endpointService.delete('ep-1')
      expect(api.delete).toHaveBeenCalledWith('/endpoints/ep-1')
    })
  })
})
