from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse, Response as StarletteResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.cache.redis import cache_get, cache_set
from src.db.session import get_db
from src.models.application import Application
from src.models.controller import Controller
from src.models.endpoint import ApiEndpoint, AuthInherit, ResponseBodyType
from src.models.auth_config import AuthConfig
from src.mock_runtime.auth_validator import validate_auth
from src.mock_runtime.resolver import match_endpoint, normalize_path
from src.mock_runtime.template_engine import render_template
from src.mock_runtime.validator import validate_request_params, validate_request_body

router = APIRouter(tags=["mock-runtime"])


def resolve_effective_auth(
    endpoint: ApiEndpoint,
    controller: Controller,
    application: Application,
) -> AuthConfig | None:
    if endpoint.auth_inherit == AuthInherit.OVERRIDE_OFF:
        return None
    if endpoint.auth_inherit == AuthInherit.OVERRIDE_ON:
        return endpoint.auth_config
    if controller.auth_config:
        return controller.auth_config
    if application.auth_config:
        return application.auth_config
    return None


@router.api_route(
    "/mock/{app_slug}/{mock_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
)
async def handle_mock_request(
    app_slug: str,
    mock_path: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Application)
        .where(Application.slug == app_slug, Application.deleted_at.is_(None))
        .options(selectinload(Application.auth_config))
    )
    result = await db.execute(query)
    application = result.scalar_one_or_none()

    if not application:
        return JSONResponse(
            status_code=404,
            content={"error": "APPLICATION_NOT_FOUND", "message": f"Application '{app_slug}' not found."},
        )

    if not application.is_enabled:
        return JSONResponse(
            status_code=503,
            content={"error": "APPLICATION_DISABLED", "message": "This mock application is currently disabled."},
        )

    c_query = (
        select(Controller)
        .where(
            Controller.application_id == application.id,
            Controller.deleted_at.is_(None),
            Controller.is_enabled.is_(True),
        )
        .options(
            selectinload(Controller.auth_config),
            selectinload(Controller.endpoints).selectinload(ApiEndpoint.auth_config),
            selectinload(Controller.endpoints).selectinload(ApiEndpoint.response_headers),
            selectinload(Controller.endpoints).selectinload(ApiEndpoint.request_params),
            selectinload(Controller.endpoints).selectinload(ApiEndpoint.request_body),
        )
    )
    c_res = await db.execute(c_query)
    controllers = c_res.scalars().all()

    all_endpoints: list[ApiEndpoint] = []
    ctrl_map: dict[str, Controller] = {}
    for ctrl in controllers:
        for ep in ctrl.endpoints:
            if ep.deleted_at is None and ep.is_enabled:
                all_endpoints.append(ep)
                ctrl_map[str(ep.id)] = ctrl

    matched_ep, path_params = match_endpoint(
        method=request.method,
        path="/" + mock_path,
        endpoints=all_endpoints,
    )

    if not matched_ep:
        return JSONResponse(
            status_code=404,
            content={
                "error": "ENDPOINT_NOT_FOUND",
                "message": f"No active mock endpoint matches {request.method} /{mock_path} in application '{app_slug}'.",
            },
        )

    parent_ctrl = ctrl_map[str(matched_ep.id)]

    effective_auth = resolve_effective_auth(matched_ep, parent_ctrl, application)
    req_headers = dict(request.headers)
    auth_res = validate_auth(effective_auth, req_headers)
    if not auth_res.is_valid:
        return JSONResponse(
            status_code=auth_res.status_code,
            content={"error": "UNAUTHORIZED", "message": auth_res.error_message},
        )

    query_params = dict(request.query_params)

    # Validate Query & Header request parameters
    param_val_res = validate_request_params(matched_ep.request_params, query_params, req_headers)
    if not param_val_res.is_valid:
        return JSONResponse(
            status_code=param_val_res.status_code,
            content={"error": "INVALID_REQUEST_PARAMETERS", "message": param_val_res.error_message},
        )

    raw_body = await request.body()
    parsed_body = None
    try:
        if req_headers.get("content-type", "").startswith("application/json"):
            import json
            parsed_body = json.loads(raw_body.decode("utf-8")) if raw_body else None
    except Exception:
        parsed_body = None

    # Validate Request Body
    body_val_res = validate_request_body(matched_ep.request_body, raw_body, parsed_body)
    if not body_val_res.is_valid:
        return JSONResponse(
            status_code=body_val_res.status_code,
            content={"error": "INVALID_REQUEST_BODY", "message": body_val_res.error_message},
        )

    context = {
        "request": {
            "query": query_params,
            "path": path_params,
            "header": req_headers,
            "body": parsed_body,
        }
    }

    if matched_ep.response_delay_ms > 0:
        delay_sec = min(matched_ep.response_delay_ms, 10000) / 1000.0
        await asyncio.sleep(delay_sec)

    custom_headers: dict[str, str] = {}
    for rh in matched_ep.response_headers:
        custom_headers[rh.name] = str(render_template(rh.value, context))

    status_code = matched_ep.response_status or 200

    if matched_ep.response_body_type == ResponseBodyType.EMPTY:
        return StarletteResponse(
            content=b"",
            status_code=status_code,
            headers=custom_headers,
        )

    if matched_ep.response_body_type == ResponseBodyType.TEXT:
        raw_text = str(matched_ep.response_body or "")
        rendered_text = render_template(raw_text, context)
        return PlainTextResponse(
            content=str(rendered_text),
            status_code=status_code,
            headers=custom_headers,
        )

    body_data = matched_ep.response_body
    rendered_json = render_template(body_data, context)
    return JSONResponse(
        content=rendered_json,
        status_code=status_code,
        headers=custom_headers,
    )
