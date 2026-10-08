from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_controllers_and_endpoints_lifecycle(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    # 1. Create Application
    app_res = await client.post(
        "/api/v1/applications",
        json={"name": "Store App", "description": "E-commerce APIs"},
        headers=auth_headers,
    )
    assert app_res.status_code == 201
    app_id = app_res.json()["id"]

    # 2. Create Controller
    ctrl_res = await client.post(
        f"/api/v1/applications/{app_id}/controllers",
        json={"name": "Products Controller", "description": "Endpoints for product catalog", "position": 1},
        headers=auth_headers,
    )
    assert ctrl_res.status_code == 201
    ctrl_data = ctrl_res.json()
    assert ctrl_data["name"] == "Products Controller"
    ctrl_id = ctrl_data["id"]

    # 3. List Controllers
    ctrl_list = await client.get(f"/api/v1/applications/{app_id}/controllers", headers=auth_headers)
    assert ctrl_list.status_code == 200
    assert any(c["id"] == ctrl_id for c in ctrl_list.json())

    # 4. Get Controller
    get_ctrl = await client.get(f"/api/v1/controllers/{ctrl_id}", headers=auth_headers)
    assert get_ctrl.status_code == 200
    assert get_ctrl.json()["name"] == "Products Controller"

    # 5. Update Controller
    update_ctrl = await client.patch(
        f"/api/v1/controllers/{ctrl_id}",
        json={
            "name": "Catalog Controller",
            "auth_config": {
                "auth_type": "bearer",
                "bearer_token": "token-12345",
            },
        },
        headers=auth_headers,
    )
    assert update_ctrl.status_code == 200
    assert update_ctrl.json()["name"] == "Catalog Controller"
    assert update_ctrl.json()["auth_config"]["auth_type"] == "bearer"

    # 6. Toggle Controller
    toggle_ctrl = await client.patch(f"/api/v1/controllers/{ctrl_id}/toggle", headers=auth_headers)
    assert toggle_ctrl.status_code == 200
    assert toggle_ctrl.json()["is_enabled"] is False

    # Toggle back on
    await client.patch(f"/api/v1/controllers/{ctrl_id}/toggle", headers=auth_headers)

    # 7. Create Endpoint
    ep_payload = {
        "name": "List Products",
        "description": "Returns mock product list",
        "method": "GET",
        "path": "/products",
        "response_status": 200,
        "response_body": {"products": [{"id": "{{uuid}}", "name": "Keyboard"}]},
        "response_body_type": "json",
        "response_delay_ms": 0,
        "auth_inherit": "inherit",
        "request_params": [
            {
                "param_type": "query",
                "name": "limit",
                "value_type": "integer",
                "required": False,
                "default_val": "10",
            }
        ],
        "response_headers": [
            {"name": "X-Custom-Header", "value": "MockEase-Test"}
        ],
    }
    create_ep = await client.post(
        f"/api/v1/controllers/{ctrl_id}/endpoints",
        json=ep_payload,
        headers=auth_headers,
    )
    assert create_ep.status_code == 201
    ep_data = create_ep.json()
    assert ep_data["name"] == "List Products"
    assert ep_data["method"] == "GET"
    assert ep_data["path"] == "/products"
    ep_id = ep_data["id"]

    # 8. List Endpoints for Controller
    ep_list = await client.get(f"/api/v1/controllers/{ctrl_id}/endpoints", headers=auth_headers)
    assert ep_list.status_code == 200
    assert any(e["id"] == ep_id for e in ep_list.json())

    # 9. Get Endpoint by ID
    get_ep = await client.get(f"/api/v1/endpoints/{ep_id}", headers=auth_headers)
    assert get_ep.status_code == 200
    assert get_ep.json()["name"] == "List Products"

    # 10. Update Endpoint
    update_ep = await client.patch(
        f"/api/v1/endpoints/{ep_id}",
        json={
            "name": "List Products (Updated)",
            "response_status": 201,
            "auth_inherit": "override_off",
        },
        headers=auth_headers,
    )
    assert update_ep.status_code == 200
    assert update_ep.json()["name"] == "List Products (Updated)"
    assert update_ep.json()["response_status"] == 201

    # 11. Toggle Endpoint
    toggle_ep = await client.patch(f"/api/v1/endpoints/{ep_id}/toggle", headers=auth_headers)
    assert toggle_ep.status_code == 200
    assert toggle_ep.json()["is_enabled"] is False

    # 12. Delete Endpoint
    del_ep = await client.delete(f"/api/v1/endpoints/{ep_id}", headers=auth_headers)
    assert del_ep.status_code == 204

    # 13. Delete Controller
    del_ctrl = await client.delete(f"/api/v1/controllers/{ctrl_id}", headers=auth_headers)
    assert del_ctrl.status_code == 204
