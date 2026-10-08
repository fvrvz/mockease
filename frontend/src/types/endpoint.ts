export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE' | 'HEAD' | 'OPTIONS'
export type AuthInherit = 'inherit' | 'override_on' | 'override_off'
export type ResponseBodyType = 'json' | 'text' | 'empty'
export type ParamType = 'query' | 'path' | 'header'
export type RequestBodyType = 'json' | 'form' | 'urlencoded' | 'raw' | 'none'

export interface RequestParam {
  id?: string
  param_type: ParamType
  name: string
  value_type: string
  required: boolean
  default_val?: string | null
  description?: string | null
}

export interface RequestBody {
  id?: string
  body_type: RequestBodyType
  schema_def?: Record<string, unknown> | null
  required: boolean
}

export interface ResponseHeader {
  id?: string
  name: string
  value: string
}

export interface ApiEndpoint {
  id: string
  controller_id: string
  name: string
  description: string | null
  method: HttpMethod
  path: string
  is_enabled: boolean
  auth_inherit: AuthInherit
  response_status: number
  response_body: Record<string, unknown> | string | null
  response_body_type: ResponseBodyType
  response_delay_ms: number
  created_at: string
  updated_at: string
  request_params?: RequestParam[]
  request_body?: RequestBody | null
  response_headers?: ResponseHeader[]
}

export interface CreateEndpointRequest {
  name: string
  description?: string
  method: HttpMethod
  path: string
  response_status?: number
  response_body?: Record<string, unknown> | string | null
  response_body_type?: ResponseBodyType
  response_delay_ms?: number
  auth_inherit?: AuthInherit
}

export interface UpdateEndpointRequest extends Partial<CreateEndpointRequest> {
  is_enabled?: boolean
  request_params?: RequestParam[]
  request_body?: RequestBody | null
  response_headers?: ResponseHeader[]
}
