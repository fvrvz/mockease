import api from './api'
import type {
  Application,
  CreateApplicationRequest,
  UpdateApplicationRequest,
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
}

