from __future__ import annotations

import uuid
from typing import Any
from pydantic import BaseModel, Field

from src.models.endpoint import HttpMethod, AuthInherit, ResponseBodyType, ParamType, RequestBodyType
from src.models.auth_config import AuthType


# --- Auth Config Schemas ---
class AuthConfigSchema(BaseModel):
    auth_type: AuthType = AuthType.NONE
    api_key_header: str | None = None
    api_key_value: str | None = None
    bearer_token: str | None = None
    basic_username: str | None = None
    basic_password: str | None = None


# --- Application Schemas ---
class ApplicationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    auth_config: AuthConfigSchema | None = None


class ApplicationUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    is_enabled: bool | None = None
    auth_config: AuthConfigSchema | None = None


class ApplicationResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    is_enabled: bool
    created_at: Any
    updated_at: Any
    controller_count: int = 0
    endpoint_count: int = 0
    enabled_endpoint_count: int = 0
    disabled_endpoint_count: int = 0
    auth_config: AuthConfigSchema | None = None


# --- Controller Schemas ---
class ControllerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    position: int = 0
    auth_config: AuthConfigSchema | None = None


class ControllerUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    is_enabled: bool | None = None
    position: int | None = None
    auth_config: AuthConfigSchema | None = None


class ControllerResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    application_id: uuid.UUID
    name: str
    description: str | None
    is_enabled: bool
    position: int
    created_at: Any
    updated_at: Any
    endpoint_count: int = 0
    auth_config: AuthConfigSchema | None = None


# --- Endpoint Sub-schemas ---
class RequestParamSchema(BaseModel):
    id: uuid.UUID | None = None
    param_type: ParamType
    name: str
    value_type: str = "string"
    required: bool = False
    default_val: str | None = None
    description: str | None = None


class RequestBodySchema(BaseModel):
    id: uuid.UUID | None = None
    body_type: RequestBodyType = RequestBodyType.NONE
    schema_def: dict[str, Any] | None = None
    required: bool = False


class ResponseHeaderSchema(BaseModel):
    id: uuid.UUID | None = None
    name: str
    value: str


class EndpointCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    method: HttpMethod = HttpMethod.GET
    path: str = Field(..., min_length=1)
    auth_inherit: AuthInherit = AuthInherit.INHERIT
    response_status: int = 200
    response_body: Any = None
    response_body_type: ResponseBodyType = ResponseBodyType.JSON
    response_delay_ms: int = 0
    auth_config: AuthConfigSchema | None = None
    request_params: list[RequestParamSchema] = []
    request_body: RequestBodySchema | None = None
    response_headers: list[ResponseHeaderSchema] = []


class EndpointUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    method: HttpMethod | None = None
    path: str | None = None
    is_enabled: bool | None = None
    auth_inherit: AuthInherit | None = None
    response_status: int | None = None
    response_body: Any = None
    response_body_type: ResponseBodyType | None = None
    response_delay_ms: int | None = None
    auth_config: AuthConfigSchema | None = None
    request_params: list[RequestParamSchema] | None = None
    request_body: RequestBodySchema | None = None
    response_headers: list[ResponseHeaderSchema] | None = None


class EndpointResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    controller_id: uuid.UUID
    name: str
    description: str | None
    method: HttpMethod
    path: str
    is_enabled: bool
    auth_inherit: AuthInherit
    response_status: int
    response_body: Any = None
    response_body_type: ResponseBodyType
    response_delay_ms: int
    created_at: Any
    updated_at: Any
    auth_config: AuthConfigSchema | None = None
    request_params: list[RequestParamSchema] = []
    request_body: RequestBodySchema | None = None
    response_headers: list[ResponseHeaderSchema] = []

