export type AuthType = 'none' | 'api_key' | 'bearer' | 'basic'

export interface AuthConfig {
  id: string
  auth_type: AuthType
  api_key_header?: string | null
  api_key_value?: string | null
  bearer_token?: string | null
  basic_username?: string | null
  basic_password?: string | null
}

export interface Controller {
  id: string
  application_id: string
  name: string
  description: string | null
  is_enabled: boolean
  position: number
  created_at: string
  updated_at: string
  endpoint_count?: number
  auth_config?: AuthConfig | null
}

export interface CreateControllerRequest {
  name: string
  description?: string
}

export interface UpdateControllerRequest {
  name?: string
  description?: string
  is_enabled?: boolean
  position?: number
}
