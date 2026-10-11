import api from './api'
import type {
  Application,
  CreateApplicationRequest,
  UpdateApplicationRequest,
  ImportSpecRequest,
} from '@/types/application'

export const applicationService = {
  async list(): Promise<Application[]> {
    const res = await api.get<Application[]>('/applications')
    return res.data
  },

  async get(id: string): Promise<Application> {
    const res = await api.get<Application>(`/applications/${id}`)
    return res.data
  },

  async create(data: CreateApplicationRequest): Promise<Application> {
    const res = await api.post<Application>('/applications', data)
    return res.data
  },

  async update(id: string, data: UpdateApplicationRequest): Promise<Application> {
    const res = await api.patch<Application>(`/applications/${id}`, data)
    return res.data
  },

  async delete(id: string): Promise<void> {
    await api.delete(`/applications/${id}`)
  },

  async toggle(id: string): Promise<Application> {
    const res = await api.patch<Application>(`/applications/${id}/toggle`)
    return res.data
  },

  async exportOpenApi(id: string): Promise<Record<string, unknown>> {
    const res = await api.get<Record<string, unknown>>(`/applications/${id}/export/openapi`)
    return res.data
  },

  async exportPostman(id: string): Promise<Record<string, unknown>> {
    const res = await api.get<Record<string, unknown>>(`/applications/${id}/export/postman`)
    return res.data
  },

  async importOpenApi(data: ImportSpecRequest): Promise<Application> {
    const res = await api.post<Application>('/applications/import/openapi', data)
    return res.data
  },

  async importIntoApplication(id: string, data: ImportSpecRequest): Promise<Application> {
    const res = await api.post<Application>(`/applications/${id}/import/openapi`, data)
    return res.data
  },
}


