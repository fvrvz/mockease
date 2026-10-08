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
from src.models.endpoint import ApiEndpoint
from src.models.auth_config import AuthConfig
from src.schemas.entities import (
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationResponse,
    AuthConfigSchema,
)
from src.utils.slugify import unique_slug

router = APIRouter(prefix="/applications", tags=["applications"])


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


@router.get("", response_model=list[ApplicationResponse])
async def list_applications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Application)
        .where(Application.user_id == current_user.id, Application.deleted_at.is_(None))
        .options(
            selectinload(Application.auth_config),
            selectinload(Application.controllers).selectinload(Controller.endpoints),
        )
        .order_by(Application.created_at.desc())
    )
    result = await db.execute(query)
    apps = result.scalars().all()

    resp = []
    for app in apps:
        active_controllers = [c for c in app.controllers if c.deleted_at is None]
        endpoints = [
            ep for c in active_controllers for ep in c.endpoints if ep.deleted_at is None
        ]
        enabled_count = sum(1 for ep in endpoints if ep.is_enabled)
        disabled_count = len(endpoints) - enabled_count

        resp.append(
            ApplicationResponse(
                id=app.id,
                name=app.name,
                slug=app.slug,
                description=app.description,
                is_enabled=app.is_enabled,
                created_at=app.created_at,
                updated_at=app.updated_at,
                controller_count=len(active_controllers),
                endpoint_count=len(endpoints),
                enabled_endpoint_count=enabled_count,
                disabled_endpoint_count=disabled_count,
                auth_config=map_auth_config(app.auth_config),
            )
        )
    return resp


@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(
    body: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    slug = unique_slug(body.name)
    app = Application(
        user_id=current_user.id,
        name=body.name,
        slug=slug,
        description=body.description,
        is_enabled=True,
    )
    db.add(app)
    await db.flush()

    if body.auth_config:
        ac = AuthConfig(
            application_id=app.id,
            auth_type=body.auth_config.auth_type,
            api_key_header=body.auth_config.api_key_header,
            api_key_value=body.auth_config.api_key_value,
            bearer_token=body.auth_config.bearer_token,
            basic_username=body.auth_config.basic_username,
            basic_password=body.auth_config.basic_password,
        )
        db.add(ac)
        await db.flush()
        app.auth_config = ac

    return ApplicationResponse(
        id=app.id,
        name=app.name,
        slug=app.slug,
        description=app.description,
        is_enabled=app.is_enabled,
        created_at=app.created_at,
        updated_at=app.updated_at,
        controller_count=0,
        endpoint_count=0,
        enabled_endpoint_count=0,
        disabled_endpoint_count=0,
        auth_config=map_auth_config(app.auth_config),
    )


@router.get("/{app_id}", response_model=ApplicationResponse)
async def get_application(
    app_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Application)
        .where(
            Application.id == app_id,
            Application.user_id == current_user.id,
            Application.deleted_at.is_(None),
        )
        .options(
            selectinload(Application.auth_config),
            selectinload(Application.controllers).selectinload(Controller.endpoints),
        )
    )
    result = await db.execute(query)
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    active_controllers = [c for c in app.controllers if c.deleted_at is None]
    endpoints = [
        ep for c in active_controllers for ep in c.endpoints if ep.deleted_at is None
    ]
    enabled_count = sum(1 for ep in endpoints if ep.is_enabled)

    return ApplicationResponse(
        id=app.id,
        name=app.name,
        slug=app.slug,
        description=app.description,
        is_enabled=app.is_enabled,
        created_at=app.created_at,
        updated_at=app.updated_at,
        controller_count=len(active_controllers),
        endpoint_count=len(endpoints),
        enabled_endpoint_count=enabled_count,
        disabled_endpoint_count=len(endpoints) - enabled_count,
        auth_config=map_auth_config(app.auth_config),
    )


@router.patch("/{app_id}", response_model=ApplicationResponse)
async def update_application(
    app_id: uuid.UUID,
    body: ApplicationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Application)
        .where(
            Application.id == app_id,
            Application.user_id == current_user.id,
            Application.deleted_at.is_(None),
        )
        .options(selectinload(Application.auth_config))
    )
    result = await db.execute(query)
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    if body.name is not None:
        app.name = body.name
    if body.description is not None:
        app.description = body.description
    if body.is_enabled is not None:
        app.is_enabled = body.is_enabled

    if body.auth_config is not None:
        if app.auth_config:
            app.auth_config.auth_type = body.auth_config.auth_type
            app.auth_config.api_key_header = body.auth_config.api_key_header
            app.auth_config.api_key_value = body.auth_config.api_key_value
            app.auth_config.bearer_token = body.auth_config.bearer_token
            app.auth_config.basic_username = body.auth_config.basic_username
            app.auth_config.basic_password = body.auth_config.basic_password
        else:
            ac = AuthConfig(
                application_id=app.id,
                auth_type=body.auth_config.auth_type,
                api_key_header=body.auth_config.api_key_header,
                api_key_value=body.auth_config.api_key_value,
                bearer_token=body.auth_config.bearer_token,
                basic_username=body.auth_config.basic_username,
                basic_password=body.auth_config.basic_password,
            )
            db.add(ac)
            app.auth_config = ac

    await db.flush()
    return ApplicationResponse(
        id=app.id,
        name=app.name,
        slug=app.slug,
        description=app.description,
        is_enabled=app.is_enabled,
        created_at=app.created_at,
        updated_at=app.updated_at,
        auth_config=map_auth_config(app.auth_config),
    )


@router.delete("/{app_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(
    app_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Application).where(
        Application.id == app_id,
        Application.user_id == current_user.id,
        Application.deleted_at.is_(None),
    )
    result = await db.execute(query)
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    app.deleted_at = datetime.now(timezone.utc)
    await db.flush()
    return None


@router.patch("/{app_id}/toggle", response_model=ApplicationResponse)
async def toggle_application(
    app_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Application)
        .where(
            Application.id == app_id,
            Application.user_id == current_user.id,
            Application.deleted_at.is_(None),
        )
        .options(selectinload(Application.auth_config))
    )
    result = await db.execute(query)
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    app.is_enabled = not app.is_enabled
    await db.flush()
    return ApplicationResponse(
        id=app.id,
        name=app.name,
        slug=app.slug,
        description=app.description,
        is_enabled=app.is_enabled,
        created_at=app.created_at,
        updated_at=app.updated_at,
        auth_config=map_auth_config(app.auth_config),
    )
