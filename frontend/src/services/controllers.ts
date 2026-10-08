import api from './api'
import type {
  Controller,
  CreateControllerRequest,
  UpdateControllerRequest,
} from '@/types/controller'

export const controllerService = {
  async list(appId: string): Promise<Controller[]> {
    const res = await api.get<Controller[]>(`/applications/${appId}/controllers`)
    return res.data
  },

  async get(id: string): Promise<Controller> {
    const res = await api.get<Controller>(`/controllers/${id}`)
    return res.data
  },

  async create(appId: string, data: CreateControllerRequest): Promise<Controller> {
    const res = await api.post<Controller>(`/applications/${appId}/controllers`, data)
    return res.data
  },

  async update(id: string, data: UpdateControllerRequest): Promise<Controller> {
    const res = await api.patch<Controller>(`/controllers/${id}`, data)
    return res.data
  },

  async delete(id: string): Promise<void> {
    await api.delete(`/controllers/${id}`)
  },

  async toggle(id: string): Promise<Controller> {
    const res = await api.patch<Controller>(`/controllers/${id}/toggle`)
    return res.data
  },
}
