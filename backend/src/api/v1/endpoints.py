from __future__ import annotations

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.dependencies.auth import get_current_user
from src.db.session import get_db
from src.models.user import User
from src.models.application import Application
from src.models.controller import Controller
from src.models.endpoint import (
    ApiEndpoint,
    ApiRequestParam,
    ApiRequestBody,
    ApiResponseHeader,
)
from src.models.auth_config import AuthConfig
from src.schemas.entities import (
    EndpointCreate,
    EndpointUpdate,
    EndpointResponse,
    AuthConfigSchema,
    RequestParamSchema,
    RequestBodySchema,
    ResponseHeaderSchema,
)

router = APIRouter(tags=["endpoints"])


def map_auth_config(ac: AuthConfig | None) -> AuthConfigSchema | None:
    if not ac:
        return None
    return AuthConfigSchema(
        auth_type=ac.auth_type,
        api_key_header=ac.api_key_header,
        api_key_value=ac.api_key_value,
        bearer_token=ac.bearer_token,
        basic_username=ac.basic_username,
        basic_password=ac.basic_password,
    )


def map_endpoint_response(ep: ApiEndpoint) -> EndpointResponse:
    params = [
        RequestParamSchema(
            id=p.id,
            param_type=p.param_type,
            name=p.name,
            value_type=p.value_type,
            required=p.required,
            default_val=p.default_val,
            description=p.description,
        )
        for p in (ep.request_params or [])
    ]

    body = None
    if ep.request_body:
        body = RequestBodySchema(
            id=ep.request_body.id,
            body_type=ep.request_body.body_type,
            schema_def=ep.request_body.schema_def,
            required=ep.request_body.required,
        )

    headers = [
        ResponseHeaderSchema(id=h.id, name=h.name, value=h.value)
        for h in (ep.response_headers or [])
    ]

    return EndpointResponse(
        id=ep.id,
        controller_id=ep.controller_id,
        name=ep.name,
        description=ep.description,
        method=ep.method,
        path=ep.path,
        is_enabled=ep.is_enabled,
        auth_inherit=ep.auth_inherit,
        response_status=ep.response_status,
        response_body=ep.response_body,
        response_body_type=ep.response_body_type,
        response_delay_ms=ep.response_delay_ms,
        created_at=ep.created_at,
        updated_at=ep.updated_at,
        auth_config=map_auth_config(ep.auth_config),
        request_params=params,
        request_body=body,
        response_headers=headers,
    )


@router.get("/controllers/{controller_id}/endpoints", response_model=list[EndpointResponse])
async def list_endpoints(
    controller_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Controller)
        .join(Application)
        .where(
            Controller.id == controller_id,
            Application.user_id == current_user.id,
            Controller.deleted_at.is_(None),
        )
    )
    res = await db.execute(query)
    if not res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Controller not found")

    ep_query = (
        select(ApiEndpoint)
        .where(ApiEndpoint.controller_id == controller_id, ApiEndpoint.deleted_at.is_(None))
        .options(
            selectinload(ApiEndpoint.auth_config),
            selectinload(ApiEndpoint.request_params),
            selectinload(ApiEndpoint.request_body),
            selectinload(ApiEndpoint.response_headers),
        )
        .order_by(ApiEndpoint.created_at.asc())
    )
    result = await db.execute(ep_query)
    endpoints = result.scalars().all()
    return [map_endpoint_response(ep) for ep in endpoints]


@router.post("/controllers/{controller_id}/endpoints", response_model=EndpointResponse, status_code=status.HTTP_201_CREATED)
async def create_endpoint(
    controller_id: uuid.UUID,
    body: EndpointCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Controller)
        .join(Application)
        .where(
            Controller.id == controller_id,
            Application.user_id == current_user.id,
            Controller.deleted_at.is_(None),
        )
    )
    res = await db.execute(query)
    if not res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Controller not found")

    clean_path = body.path.strip()
    if not clean_path.startswith("/"):
        clean_path = "/" + clean_path

    ep = ApiEndpoint(
        controller_id=controller_id,
        name=body.name,
        description=body.description,
        method=body.method,
        path=clean_path,
        auth_inherit=body.auth_inherit,
        response_status=body.response_status,
        response_body=body.response_body,
        response_body_type=body.response_body_type,
        response_delay_ms=body.response_delay_ms,
        is_enabled=True,
    )
    db.add(ep)
    await db.flush()

    if body.auth_config:
        ac = AuthConfig(
            endpoint_id=ep.id,
            auth_type=body.auth_config.auth_type,
            api_key_header=body.auth_config.api_key_header,
            api_key_value=body.auth_config.api_key_value,
            bearer_token=body.auth_config.bearer_token,
            basic_username=body.auth_config.basic_username,
            basic_password=body.auth_config.basic_password,
        )
        db.add(ac)
        ep.auth_config = ac

    for p in body.request_params:
        db.add(
            ApiRequestParam(
                endpoint_id=ep.id,
                param_type=p.param_type,
                name=p.name,
                value_type=p.value_type,
                required=p.required,
                default_val=p.default_val,
                description=p.description,
            )
        )

    if body.request_body:
        db.add(
            ApiRequestBody(
                endpoint_id=ep.id,
                body_type=body.request_body.body_type,
                schema_def=body.request_body.schema_def,
                required=body.request_body.required,
            )
        )

    for h in body.response_headers:
        db.add(ApiResponseHeader(endpoint_id=ep.id, name=h.name, value=h.value))

    await db.flush()

    full_query = (
        select(ApiEndpoint)
        .where(ApiEndpoint.id == ep.id)
        .options(
            selectinload(ApiEndpoint.auth_config),
            selectinload(ApiEndpoint.request_params),
            selectinload(ApiEndpoint.request_body),
            selectinload(ApiEndpoint.response_headers),
        )
    )
    reloaded = (await db.execute(full_query)).scalar_one()
    return map_endpoint_response(reloaded)


@router.get("/endpoints/{endpoint_id}", response_model=EndpointResponse)
async def get_endpoint(
    endpoint_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(ApiEndpoint)
        .join(Controller)
        .join(Application)
        .where(
            ApiEndpoint.id == endpoint_id,
            Application.user_id == current_user.id,
            ApiEndpoint.deleted_at.is_(None),
        )
        .options(
            selectinload(ApiEndpoint.auth_config),
            selectinload(ApiEndpoint.request_params),
            selectinload(ApiEndpoint.request_body),
            selectinload(ApiEndpoint.response_headers),
        )
    )
    result = await db.execute(query)
    ep = result.scalar_one_or_none()
    if not ep:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    return map_endpoint_response(ep)


@router.patch("/endpoints/{endpoint_id}", response_model=EndpointResponse)
async def update_endpoint(
    endpoint_id: uuid.UUID,
    body: EndpointUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(ApiEndpoint)
        .join(Controller)
        .join(Application)
        .where(
            ApiEndpoint.id == endpoint_id,
            Application.user_id == current_user.id,
            ApiEndpoint.deleted_at.is_(None),
        )
        .options(
            selectinload(ApiEndpoint.auth_config),
            selectinload(ApiEndpoint.request_params),
            selectinload(ApiEndpoint.request_body),
            selectinload(ApiEndpoint.response_headers),
        )
    )
    result = await db.execute(query)
    ep = result.scalar_one_or_none()
    if not ep:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    if body.name is not None:
        ep.name = body.name
    if body.description is not None:
        ep.description = body.description
    if body.method is not None:
        ep.method = body.method
    if body.path is not None:
        p = body.path.strip()
        ep.path = "/" + p if not p.startswith("/") else p
    if body.is_enabled is not None:
        ep.is_enabled = body.is_enabled
    if body.auth_inherit is not None:
        ep.auth_inherit = body.auth_inherit
    if body.response_status is not None:
        ep.response_status = body.response_status
    if body.response_body is not None:
        ep.response_body = body.response_body
    if body.response_body_type is not None:
        ep.response_body_type = body.response_body_type
    if body.response_delay_ms is not None:
        ep.response_delay_ms = body.response_delay_ms

    if body.auth_config is not None:
        if ep.auth_config:
            ep.auth_config.auth_type = body.auth_config.auth_type
            ep.auth_config.api_key_header = body.auth_config.api_key_header
            ep.auth_config.api_key_value = body.auth_config.api_key_value
            ep.auth_config.bearer_token = body.auth_config.bearer_token
            ep.auth_config.basic_username = body.auth_config.basic_username
            ep.auth_config.basic_password = body.auth_config.basic_password
        else:
            ac = AuthConfig(
                endpoint_id=ep.id,
                auth_type=body.auth_config.auth_type,
                api_key_header=body.auth_config.api_key_header,
                api_key_value=body.auth_config.api_key_value,
                bearer_token=body.auth_config.bearer_token,
                basic_username=body.auth_config.basic_username,
                basic_password=body.auth_config.basic_password,
            )
            db.add(ac)
            ep.auth_config = ac

    if body.request_params is not None:
        for p in ep.request_params:
            await db.delete(p)
        for p in body.request_params:
            db.add(
                ApiRequestParam(
                    endpoint_id=ep.id,
                    param_type=p.param_type,
                    name=p.name,
                    value_type=p.value_type,
                    required=p.required,
                    default_val=p.default_val,
                    description=p.description,
                )
            )

    if body.request_body is not None:
        if ep.request_body:
            await db.delete(ep.request_body)
        db.add(
            ApiRequestBody(
                endpoint_id=ep.id,
                body_type=body.request_body.body_type,
                schema_def=body.request_body.schema_def,
                required=body.request_body.required,
            )
        )

    if body.response_headers is not None:
        for h in ep.response_headers:
            await db.delete(h)
        for h in body.response_headers:
            db.add(ApiResponseHeader(endpoint_id=ep.id, name=h.name, value=h.value))

    await db.flush()

    full_query = (
        select(ApiEndpoint)
        .where(ApiEndpoint.id == ep.id)
        .options(
            selectinload(ApiEndpoint.auth_config),
            selectinload(ApiEndpoint.request_params),
            selectinload(ApiEndpoint.request_body),
            selectinload(ApiEndpoint.response_headers),
        )
    )
    reloaded = (await db.execute(full_query)).scalar_one()
    return map_endpoint_response(reloaded)


@router.delete("/endpoints/{endpoint_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_endpoint(
    endpoint_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(ApiEndpoint)
        .join(Controller)
        .join(Application)
        .where(
            ApiEndpoint.id == endpoint_id,
            Application.user_id == current_user.id,
            ApiEndpoint.deleted_at.is_(None),
        )
    )
    result = await db.execute(query)
    ep = result.scalar_one_or_none()
    if not ep:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    ep.deleted_at = datetime.now(timezone.utc)
    await db.flush()
    return None


@router.patch("/endpoints/{endpoint_id}/toggle", response_model=EndpointResponse)
async def toggle_endpoint(
    endpoint_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(ApiEndpoint)
        .join(Controller)
        .join(Application)
        .where(
            ApiEndpoint.id == endpoint_id,
            Application.user_id == current_user.id,
            ApiEndpoint.deleted_at.is_(None),
        )
        .options(
            selectinload(ApiEndpoint.auth_config),
            selectinload(ApiEndpoint.request_params),
            selectinload(ApiEndpoint.request_body),
            selectinload(ApiEndpoint.response_headers),
        )
    )
    result = await db.execute(query)
    ep = result.scalar_one_or_none()
    if not ep:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    ep.is_enabled = not ep.is_enabled
    await db.flush()
    return map_endpoint_response(ep)
