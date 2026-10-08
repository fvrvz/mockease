import type { AuthConfig } from './controller'

export interface Application {
  id: string
  user_id: string
  name: string
  slug: string
  description: string | null
  is_enabled: boolean
  created_at: string
  updated_at: string
  controller_count?: number
  endpoint_count?: number
  enabled_endpoint_count?: number
  disabled_endpoint_count?: number
  auth_config?: AuthConfig | null
}

export interface CreateApplicationRequest {
  name: string
  description?: string
}

export interface UpdateApplicationRequest {
  name?: string
  description?: string
  is_enabled?: boolean
  auth_config?: Partial<AuthConfig> | null
}

