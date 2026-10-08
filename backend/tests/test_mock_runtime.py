from __future__ import annotations

import base64
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_mock_runtime_execution_and_templating(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    # 1. Create App
    app_res = await client.post(
        "/api/v1/applications",
        json={"name": "Mock Test App", "description": "App for runtime testing"},
        headers=auth_headers,
    )
    assert app_res.status_code == 201
    app_data = app_res.json()
    app_slug = app_data["slug"]
    app_id = app_data["id"]

    # 2. Create Controller
    ctrl_res = await client.post(
        f"/api/v1/applications/{app_id}/controllers",
        json={"name": "Users", "description": "User routes"},
        headers=auth_headers,
    )
    assert ctrl_res.status_code == 201
    ctrl_id = ctrl_res.json()["id"]

    # 3. Create Endpoint with templates, query param, and headers
    ep_payload = {
        "name": "Get User Details",
        "method": "GET",
        "path": "/users/{user_id}",
        "response_status": 200,
        "response_body": {
            "id": "{{request.path.user_id}}",
            "filter": "{{request.query.filter}}",
            "request_id": "{{uuid}}",
            "status": "active",
        },
        "response_body_type": "json",
        "response_delay_ms": 0,
        "auth_inherit": "inherit",
        "response_headers": [
            {"name": "X-Mock-Powered-By", "value": "MockEase"}
        ],
    }
    ep_res = await client.post(
        f"/api/v1/controllers/{ctrl_id}/endpoints",
        json=ep_payload,
        headers=auth_headers,
    )
    assert ep_res.status_code == 201

    # 4. Invoke the mock route directly
    mock_url = f"/mock/{app_slug}/users/42?filter=admin"
    res = await client.get(mock_url)
    assert res.status_code == 200
    assert res.headers["x-mock-powered-by"] == "MockEase"
    data = res.json()
    assert data["id"] == "42"
    assert data["filter"] == "admin"
    assert len(data["request_id"]) == 36  # Valid UUID
    assert data["status"] == "active"


@pytest.mark.asyncio
async def test_mock_runtime_auth_inheritance(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    # 1. Create App with API Key Auth
    app_res = await client.post(
        "/api/v1/applications",
        json={"name": "Secured App", "description": "Protected endpoints"},
        headers=auth_headers,
    )
    app_id = app_res.json()["id"]
    app_slug = app_res.json()["slug"]

    await client.patch(
        f"/api/v1/applications/{app_id}",
        json={
            "auth_config": {
                "auth_type": "api_key",
                "api_key_header": "X-App-Key",
                "api_key_value": "super-secret-123",
            }
        },
        headers=auth_headers,
    )

    # 2. Create Controller
    ctrl_res = await client.post(
        f"/api/v1/applications/{app_id}/controllers",
        json={"name": "Secure Controller"},
        headers=auth_headers,
    )
    ctrl_id = ctrl_res.json()["id"]

    # 3. Create Inheriting Endpoint
    await client.post(
        f"/api/v1/controllers/{ctrl_id}/endpoints",
        json={
            "name": "Protected Info",
            "method": "GET",
            "path": "/info",
            "response_status": 200,
            "response_body": {"secret": "revealed"},
            "auth_inherit": "inherit",
        },
        headers=auth_headers,
    )

    # 4. Call without header -> 401
    unauth_res = await client.get(f"/mock/{app_slug}/info")
    assert unauth_res.status_code == 401

    # 5. Call with wrong key -> 403
    forbidden_res = await client.get(f"/mock/{app_slug}/info", headers={"X-App-Key": "wrong-key"})
    assert forbidden_res.status_code == 403

    # 6. Call with correct key -> 200
    valid_res = await client.get(f"/mock/{app_slug}/info", headers={"X-App-Key": "super-secret-123"})
    assert valid_res.status_code == 200
    assert valid_res.json()["secret"] == "revealed"


@pytest.mark.asyncio
async def test_mock_runtime_not_found_and_disabled(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    # Non-existent app
    missing_app = await client.get("/mock/non-existent-app-slug/test")
    assert missing_app.status_code == 404

    # Disabled app
    app_res = await client.post(
        "/api/v1/applications",
        json={"name": "To Disable App"},
        headers=auth_headers,
    )
    app_id = app_res.json()["id"]
    app_slug = app_res.json()["slug"]

    # Toggle off
    await client.patch(f"/api/v1/applications/{app_id}/toggle", headers=auth_headers)

    disabled_res = await client.get(f"/mock/{app_slug}/anything")
    assert disabled_res.status_code == 503
