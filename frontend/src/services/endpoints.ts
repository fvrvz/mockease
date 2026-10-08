import api from './api'
import type {
  ApiEndpoint,
  CreateEndpointRequest,
  UpdateEndpointRequest,
} from '@/types/endpoint'

export const endpointService = {
  async list(controllerId: string): Promise<ApiEndpoint[]> {
    const res = await api.get<ApiEndpoint[]>(`/controllers/${controllerId}/endpoints`)
    return res.data
  },

  async get(id: string): Promise<ApiEndpoint> {
    const res = await api.get<ApiEndpoint>(`/endpoints/${id}`)
    return res.data
  },

  async create(controllerId: string, data: CreateEndpointRequest): Promise<ApiEndpoint> {
    const res = await api.post<ApiEndpoint>(`/controllers/${controllerId}/endpoints`, data)
    return res.data
  },

  async update(id: string, data: UpdateEndpointRequest): Promise<ApiEndpoint> {
    const res = await api.patch<ApiEndpoint>(`/endpoints/${id}`, data)
    return res.data
  },

  async delete(id: string): Promise<void> {
    await api.delete(`/endpoints/${id}`)
  },

  async toggle(id: string): Promise<ApiEndpoint> {
    const res = await api.patch<ApiEndpoint>(`/endpoints/${id}/toggle`)
    return res.data
  },
}

