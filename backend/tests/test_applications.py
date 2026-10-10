from __future__ import annotations

import pytest
from httpx import AsyncClient

from src.models.user import User


@pytest.mark.asyncio
async def test_application_crud_lifecycle(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    # 1. Create Application
    create_payload = {
        "name": "Payments API",
        "description": "Mock service for payment testing",
    }
    res = await client.post("/api/v1/applications", json=create_payload, headers=auth_headers)
    assert res.status_code == 201
    app_data = res.json()
    assert app_data["name"] == "Payments API"
    assert "payments-api" in app_data["slug"]
    app_id = app_data["id"]

    # 2. List Applications
    list_res = await client.get("/api/v1/applications", headers=auth_headers)
    assert list_res.status_code == 200
    apps = list_res.json()
    assert any(a["id"] == app_id for a in apps)

    # 3. Get Application by ID
    get_res = await client.get(f"/api/v1/applications/{app_id}", headers=auth_headers)
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Payments API"

    # 4. Update Application
    update_payload = {
        "name": "Updated Payments API",
        "description": "Updated description",
        "is_enabled": True,
        "auth_config": {
            "auth_type": "api_key",
            "api_key_header": "X-Custom-Key",
            "api_key_value": "secret-test-key",
        },
    }
    patch_res = await client.patch(f"/api/v1/applications/{app_id}", json=update_payload, headers=auth_headers)
    assert patch_res.status_code == 200
    updated_data = patch_res.json()
    assert updated_data["name"] == "Updated Payments API"
    assert updated_data["auth_config"]["auth_type"] == "api_key"
    assert updated_data["auth_config"]["api_key_header"] == "X-Custom-Key"

    # 5. Toggle Application status
    toggle_res = await client.patch(f"/api/v1/applications/{app_id}/toggle", headers=auth_headers)
    assert toggle_res.status_code == 200
    assert toggle_res.json()["is_enabled"] is False

    # 6. Delete Application (soft delete)
    del_res = await client.delete(f"/api/v1/applications/{app_id}", headers=auth_headers)
    assert del_res.status_code == 204

    # 7. Verify Application is deleted
    get_after_del = await client.get(f"/api/v1/applications/{app_id}", headers=auth_headers)
    assert get_after_del.status_code == 404


@pytest.mark.asyncio
async def test_get_application_not_found(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    res = await client.get("/api/v1/applications/00000000-0000-0000-0000-000000000000", headers=auth_headers)
    assert res.status_code == 404
