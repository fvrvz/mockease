from __future__ import annotations

import json
import pytest
from httpx import AsyncClient

from src.services.openapi_service import _generate_sample_from_schema, OpenApiService


SAMPLE_OPENAPI_3_JSON = {
    "openapi": "3.0.0",
    "info": {
        "title": "Petstore API",
        "description": "A sample Petstore OpenAPI spec",
        "version": "1.0.0",
    },
    "paths": {
        "/pets": {
            "get": {
                "tags": ["Pets"],
                "summary": "List all pets",
                "description": "Returns a list of pets",
                "operationId": "listPets",
                "parameters": [
                    {
                        "name": "limit",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "integer", "default": 20},
                        "description": "How many items to return",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "A paged array of pets",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "integer"},
                                            "name": {"type": "string"},
                                        },
                                    },
                                }
                            }
                        },
                    }
                },
            },
            "post": {
                "tags": ["Pets"],
                "summary": "Create a pet",
                "operationId": "createPets",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "tag": {"type": "string"},
                                },
                            }
                        }
                    },
                },
                "responses": {
                    "201": {
                        "description": "Pet created",
                        "content": {
                            "application/json": {
                                "example": {"id": 1, "name": "Fluffy"}
                            }
                        },
                    }
                },
            },
        },
        "/pets/{id}": {
            "get": {
                "tags": ["Pets"],
                "summary": "Info for a specific pet",
                "parameters": [
                    {
                        "name": "id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Expected response to a valid request",
                        "content": {
                            "text/plain": {
                                "example": "Pet details text"
                            }
                        },
                    }
                },
            }
        },
    },
}

SAMPLE_OPENAPI_YAML = """
openapi: 3.0.3
info:
  title: YAML API
  description: API defined in YAML
  version: 1.0.0
paths:
  /orders:
    get:
      tags:
        - Orders
      summary: Get orders
      responses:
        '200':
          description: OK
          content:
            application/json:
              example:
                orders: []
"""

SAMPLE_SWAGGER_2_JSON = {
    "swagger": "2.0",
    "info": {
        "title": "Swagger Petstore",
        "version": "1.0.0",
    },
    "paths": {
        "/store/inventory": {
            "get": {
                "tags": ["Store"],
                "summary": "Returns pet inventories",
                "responses": {
                    "200": {
                        "description": "successful operation",
                        "schema": {
                            "type": "object",
                            "properties": {
                                "available": {"type": "integer"}
                            }
                        }
                    }
                }
            }
        }
    }
}

SAMPLE_POSTMAN_JSON = {
    "info": {
        "name": "Mock Postman Collection",
        "description": "Exported from Postman",
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
    },
    "item": [
        {
            "name": "Authentication",
            "item": [
                {
                    "name": "Login User",
                    "request": {
                        "method": "POST",
                        "header": [
                            {"key": "Content-Type", "value": "application/json"}
                        ],
                        "url": {
                            "raw": "https://api.example.com/mock/auth-app/auth/login?source=web",
                            "path": ["mock", "auth-app", "auth", "login"],
                            "query": [
                                {"key": "source", "value": "web", "description": "Client source"}
                            ]
                        }
                    },
                    "response": [
                        {
                            "code": 200,
                            "body": '{"token": "mock-jwt-token"}'
                        }
                    ]
                }
            ]
        }
    ]
}


def test_generate_sample_from_schema_unit() -> None:
    # Test invalid non-dict schema
    assert _generate_sample_from_schema(None) == {}  # type: ignore[arg-type]

    # Test explicit example & default
    assert _generate_sample_from_schema({"example": "my-example"}) == "my-example"
    assert _generate_sample_from_schema({"default": 42}) == 42

    # String types & formats
    assert _generate_sample_from_schema({"type": "string", "format": "date-time"}) == "2026-10-11T12:00:00Z"
    assert _generate_sample_from_schema({"type": "string", "format": "date"}) == "2026-10-11"
    assert _generate_sample_from_schema({"type": "string", "format": "uuid"}) == "3fa85f64-5717-4562-b3fc-2c963f66afa6"
    assert _generate_sample_from_schema({"type": "string", "format": "email"}) == "user@example.com"
    assert _generate_sample_from_schema({"type": "string", "format": "uri"}) == "https://example.com"
    assert _generate_sample_from_schema({"type": "string", "enum": ["apple", "banana"]}) == "apple"
    assert _generate_sample_from_schema({"type": "string"}) == "sample_string"

    # Numbers and booleans
    assert _generate_sample_from_schema({"type": "integer"}) == 0
    assert _generate_sample_from_schema({"type": "number"}) == 0
    assert _generate_sample_from_schema({"type": "boolean"}) is True

    # Array
    assert _generate_sample_from_schema({"type": "array", "items": {"type": "integer"}}) == [0]
    assert _generate_sample_from_schema({"type": "array"}) == []

    # Object
    obj_sample = _generate_sample_from_schema({
        "type": "object",
        "properties": {
            "active": {"type": "boolean"},
            "count": {"type": "integer"}
        }
    })
    assert obj_sample == {"active": True, "count": 0}

    # Unknown type
    assert _generate_sample_from_schema({"type": "custom_unknown"}) == {}


@pytest.mark.asyncio
async def test_import_openapi_3_json(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    res = await client.post(
        "/api/v1/applications/import/openapi",
        json={"spec": SAMPLE_OPENAPI_3_JSON, "name": "Imported Petstore"},
        headers=auth_headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Imported Petstore"
    assert data["controller_count"] >= 1
    assert data["endpoint_count"] >= 3
    app_id = data["id"]

    # Export back as OpenAPI
    export_res = await client.get(f"/api/v1/applications/{app_id}/export/openapi", headers=auth_headers)
    assert export_res.status_code == 200
    export_spec = export_res.json()
    assert export_spec["openapi"] == "3.0.3"
    assert export_spec["info"]["title"] == "Imported Petstore"
    assert "/pets" in export_spec["paths"]
    assert "get" in export_spec["paths"]["/pets"]
    assert "post" in export_spec["paths"]["/pets"]

    # Export back as Postman
    postman_res = await client.get(f"/api/v1/applications/{app_id}/export/postman", headers=auth_headers)
    assert postman_res.status_code == 200
    postman_spec = postman_res.json()
    assert postman_spec["info"]["name"] == "Imported Petstore"
    assert len(postman_spec["item"]) >= 1


@pytest.mark.asyncio
async def test_import_openapi_yaml(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    res = await client.post(
        "/api/v1/applications/import/openapi",
        json={"spec": SAMPLE_OPENAPI_YAML},
        headers=auth_headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "YAML API"
    assert data["endpoint_count"] == 1


@pytest.mark.asyncio
async def test_import_swagger_2_json(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    res = await client.post(
        "/api/v1/applications/import/openapi",
        json={"spec": SAMPLE_SWAGGER_2_JSON},
        headers=auth_headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Swagger Petstore"
    assert data["endpoint_count"] == 1


@pytest.mark.asyncio
async def test_import_postman_collection(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    res = await client.post(
        "/api/v1/applications/import/openapi",
        json={"spec": SAMPLE_POSTMAN_JSON},
        headers=auth_headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Mock Postman Collection"
    assert data["endpoint_count"] == 1


@pytest.mark.asyncio
async def test_import_into_existing_application(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    # 1. Create initial app
    create_res = await client.post(
        "/api/v1/applications",
        json={"name": "Existing App", "description": "Existing app"},
        headers=auth_headers,
    )
    assert create_res.status_code == 201
    app_id = create_res.json()["id"]

    # 2. Merge Petstore spec into existing app
    merge_res = await client.post(
        f"/api/v1/applications/{app_id}/import/openapi",
        json={"spec": SAMPLE_OPENAPI_3_JSON},
        headers=auth_headers,
    )
    assert merge_res.status_code == 200
    merged_data = merge_res.json()
    assert merged_data["endpoint_count"] >= 3

    # 3. Merging again with same spec should avoid duplicate endpoints
    merge_res_2 = await client.post(
        f"/api/v1/applications/{app_id}/import/openapi",
        json={"spec": SAMPLE_OPENAPI_3_JSON},
        headers=auth_headers,
    )
    assert merge_res_2.status_code == 200
    assert merge_res_2.json()["endpoint_count"] == merged_data["endpoint_count"]


@pytest.mark.asyncio
async def test_export_with_auth_config(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    # Create app with Bearer Auth
    create_res = await client.post(
        "/api/v1/applications",
        json={
            "name": "Auth App",
            "auth_config": {"auth_type": "bearer", "bearer_token": "token123"}
        },
        headers=auth_headers,
    )
    app_id = create_res.json()["id"]

    # Export openapi
    export_res = await client.get(f"/api/v1/applications/{app_id}/export/openapi", headers=auth_headers)
    assert export_res.status_code == 200
    spec = export_res.json()
    assert "components" in spec
    assert "BearerAuth" in spec["components"]["securitySchemes"]

    # Update app with API Key
    await client.patch(
        f"/api/v1/applications/{app_id}",
        json={"auth_config": {"auth_type": "api_key", "api_key_header": "X-Token"}},
        headers=auth_headers,
    )
    export_res2 = await client.get(f"/api/v1/applications/{app_id}/export/openapi", headers=auth_headers)
    assert export_res2.status_code == 200
    spec2 = export_res2.json()
    assert "ApiKeyAuth" in spec2["components"]["securitySchemes"]

    # Update app with Basic Auth
    await client.patch(
        f"/api/v1/applications/{app_id}",
        json={"auth_config": {"auth_type": "basic"}},
        headers=auth_headers,
    )
    export_res3 = await client.get(f"/api/v1/applications/{app_id}/export/openapi", headers=auth_headers)
    assert export_res3.status_code == 200
    spec3 = export_res3.json()
    assert "BasicAuth" in spec3["components"]["securitySchemes"]


@pytest.mark.asyncio
async def test_import_invalid_spec_returns_400(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    res = await client.post(
        "/api/v1/applications/import/openapi",
        json={"spec": "invalid: [unclosed: {"},
        headers=auth_headers,
    )
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_export_not_found(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    res1 = await client.get("/api/v1/applications/00000000-0000-0000-0000-000000000000/export/openapi", headers=auth_headers)
    assert res1.status_code == 404

    res2 = await client.get("/api/v1/applications/00000000-0000-0000-0000-000000000000/export/postman", headers=auth_headers)
    assert res2.status_code == 404

    res3 = await client.post(
        "/api/v1/applications/00000000-0000-0000-0000-000000000000/import/openapi",
        json={"spec": SAMPLE_OPENAPI_3_JSON},
        headers=auth_headers,
    )
    assert res3.status_code == 404
