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
from src.models.auth_config import AuthConfig
from src.schemas.entities import (
    ControllerCreate,
    ControllerUpdate,
    ControllerResponse,
    AuthConfigSchema,
)

router = APIRouter(tags=["controllers"])


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


@router.get("/applications/{app_id}/controllers", response_model=list[ControllerResponse])
async def list_controllers(
    app_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    app_query = select(Application).where(
        Application.id == app_id,
        Application.user_id == current_user.id,
        Application.deleted_at.is_(None),
    )
    app_res = await db.execute(app_query)
    if not app_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Application not found")

    query = (
        select(Controller)
        .where(Controller.application_id == app_id, Controller.deleted_at.is_(None))
        .options(
            selectinload(Controller.auth_config),
            selectinload(Controller.endpoints),
        )
        .order_by(Controller.position.asc(), Controller.created_at.asc())
    )
    result = await db.execute(query)
    controllers = result.scalars().all()

    return [
        ControllerResponse(
            id=c.id,
            application_id=c.application_id,
            name=c.name,
            description=c.description,
            is_enabled=c.is_enabled,
            position=c.position,
            created_at=c.created_at,
            updated_at=c.updated_at,
            endpoint_count=len([ep for ep in c.endpoints if ep.deleted_at is None]),
            auth_config=map_auth_config(c.auth_config),
        )
        for c in controllers
    ]


@router.post("/applications/{app_id}/controllers", response_model=ControllerResponse, status_code=status.HTTP_201_CREATED)
async def create_controller(
    app_id: uuid.UUID,
    body: ControllerCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    app_query = select(Application).where(
        Application.id == app_id,
        Application.user_id == current_user.id,
        Application.deleted_at.is_(None),
    )
    app_res = await db.execute(app_query)
    if not app_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Application not found")

    ctrl = Controller(
        application_id=app_id,
        name=body.name,
        description=body.description,
        position=body.position,
        is_enabled=True,
    )
    db.add(ctrl)
    await db.flush()

    if body.auth_config:
        ac = AuthConfig(
            controller_id=ctrl.id,
            auth_type=body.auth_config.auth_type,
            api_key_header=body.auth_config.api_key_header,
            api_key_value=body.auth_config.api_key_value,
            bearer_token=body.auth_config.bearer_token,
            basic_username=body.auth_config.basic_username,
            basic_password=body.auth_config.basic_password,
        )
        db.add(ac)
        await db.flush()
        ctrl.auth_config = ac

    reloaded_ctrl_q = (
        select(Controller)
        .where(Controller.id == ctrl.id)
        .options(selectinload(Controller.auth_config))
    )
    reloaded_ctrl = (await db.execute(reloaded_ctrl_q)).scalar_one()

    return ControllerResponse(
        id=reloaded_ctrl.id,
        application_id=reloaded_ctrl.application_id,
        name=reloaded_ctrl.name,
        description=reloaded_ctrl.description,
        is_enabled=reloaded_ctrl.is_enabled,
        position=reloaded_ctrl.position,
        created_at=reloaded_ctrl.created_at,
        updated_at=reloaded_ctrl.updated_at,
        endpoint_count=0,
        auth_config=map_auth_config(reloaded_ctrl.auth_config),
    )



@router.get("/controllers/{controller_id}", response_model=ControllerResponse)
async def get_controller(
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
        .options(
            selectinload(Controller.auth_config),
            selectinload(Controller.endpoints),
        )
    )
    result = await db.execute(query)
    ctrl = result.scalar_one_or_none()
    if not ctrl:
        raise HTTPException(status_code=404, detail="Controller not found")

    return ControllerResponse(
        id=ctrl.id,
        application_id=ctrl.application_id,
        name=ctrl.name,
        description=ctrl.description,
        is_enabled=ctrl.is_enabled,
        position=ctrl.position,
        created_at=ctrl.created_at,
        updated_at=ctrl.updated_at,
        endpoint_count=len([ep for ep in ctrl.endpoints if ep.deleted_at is None]),
        auth_config=map_auth_config(ctrl.auth_config),
    )


@router.patch("/controllers/{controller_id}", response_model=ControllerResponse)
async def update_controller(
    controller_id: uuid.UUID,
    body: ControllerUpdate,
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
        .options(selectinload(Controller.auth_config))
    )
    result = await db.execute(query)
    ctrl = result.scalar_one_or_none()
    if not ctrl:
        raise HTTPException(status_code=404, detail="Controller not found")

    if body.name is not None:
        ctrl.name = body.name
    if body.description is not None:
        ctrl.description = body.description
    if body.is_enabled is not None:
        ctrl.is_enabled = body.is_enabled
    if body.position is not None:
        ctrl.position = body.position

    if body.auth_config is not None:
        if ctrl.auth_config:
            ctrl.auth_config.auth_type = body.auth_config.auth_type
            ctrl.auth_config.api_key_header = body.auth_config.api_key_header
            ctrl.auth_config.api_key_value = body.auth_config.api_key_value
            ctrl.auth_config.bearer_token = body.auth_config.bearer_token
            ctrl.auth_config.basic_username = body.auth_config.basic_username
            ctrl.auth_config.basic_password = body.auth_config.basic_password
        else:
            ac = AuthConfig(
                controller_id=ctrl.id,
                auth_type=body.auth_config.auth_type,
                api_key_header=body.auth_config.api_key_header,
                api_key_value=body.auth_config.api_key_value,
                bearer_token=body.auth_config.bearer_token,
                basic_username=body.auth_config.basic_username,
                basic_password=body.auth_config.basic_password,
            )
            db.add(ac)
            ctrl.auth_config = ac

    await db.flush()
    return ControllerResponse(
        id=ctrl.id,
        application_id=ctrl.application_id,
        name=ctrl.name,
        description=ctrl.description,
        is_enabled=ctrl.is_enabled,
        position=ctrl.position,
        created_at=ctrl.created_at,
        updated_at=ctrl.updated_at,
        auth_config=map_auth_config(ctrl.auth_config),
    )


@router.delete("/controllers/{controller_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_controller(
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
    result = await db.execute(query)
    ctrl = result.scalar_one_or_none()
    if not ctrl:
        raise HTTPException(status_code=404, detail="Controller not found")

    ctrl.deleted_at = datetime.now(timezone.utc)
    await db.flush()
    return None


@router.patch("/controllers/{controller_id}/toggle", response_model=ControllerResponse)
async def toggle_controller(
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
        .options(selectinload(Controller.auth_config))
    )
    result = await db.execute(query)
    ctrl = result.scalar_one_or_none()
    if not ctrl:
        raise HTTPException(status_code=404, detail="Controller not found")

    ctrl.is_enabled = not ctrl.is_enabled
    await db.flush()
    return ControllerResponse(
        id=ctrl.id,
        application_id=ctrl.application_id,
        name=ctrl.name,
        description=ctrl.description,
        is_enabled=ctrl.is_enabled,
        position=ctrl.position,
        created_at=ctrl.created_at,
        updated_at=ctrl.updated_at,
        auth_config=map_auth_config(ctrl.auth_config),
    )
