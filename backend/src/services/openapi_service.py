from __future__ import annotations

import json
import re
import uuid
from typing import Any
import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.application import Application
from src.models.controller import Controller
from src.models.endpoint import (
    ApiEndpoint,
    ApiRequestParam,
    ApiRequestBody,
    HttpMethod,
    ParamType,
    RequestBodyType,
    ResponseBodyType,
)
from src.utils.slugify import unique_slug



def _generate_sample_from_schema(schema: dict[str, Any]) -> Any:
    """Generate a realistic mock value from a JSON schema definition."""
    if not isinstance(schema, dict):
        return {}

    # If example or default is provided in schema, use it
    if "example" in schema:
        return schema["example"]
    if "default" in schema:
        return schema["default"]

    schema_type = schema.get("type", "object")

    if schema_type == "string":
        fmt = schema.get("format", "")
        if fmt == "date-time":
            return "2026-10-11T12:00:00Z"
        if fmt == "date":
            return "2026-10-11"
        if fmt == "uuid":
            return "3fa85f64-5717-4562-b3fc-2c963f66afa6"
        if fmt == "email":
            return "user@example.com"
        if fmt == "uri":
            return "https://example.com"
        enum_vals = schema.get("enum")
        if enum_vals and len(enum_vals) > 0:
            return enum_vals[0]
        return "sample_string"

    if schema_type in ("integer", "number"):
        return 0

    if schema_type == "boolean":
        return True

    if schema_type == "array":
        items_schema = schema.get("items", {})
        if items_schema:
            return [_generate_sample_from_schema(items_schema)]
        return []

    if schema_type == "object" or "properties" in schema:
        properties = schema.get("properties", {})
        res = {}
        for prop_name, prop_schema in properties.items():
            res[prop_name] = _generate_sample_from_schema(prop_schema)
        return res

    return {}


class OpenApiService:
    """Service to export and import OpenAPI 3.0 / Swagger and Postman collections."""

    @staticmethod
    def export_to_openapi(application: Application) -> dict[str, Any]:
        """Export an application into an OpenAPI 3.0.3 specification dictionary."""
        tags = []
        paths: dict[str, dict[str, Any]] = {}

        controllers = [c for c in application.controllers if c.deleted_at is None]

        for ctrl in controllers:
            tags.append({
                "name": ctrl.name,
                "description": ctrl.description or f"Endpoints under {ctrl.name}",
            })

            endpoints = [ep for ep in ctrl.endpoints if ep.deleted_at is None]
            for ep in endpoints:
                norm_path = ep.path if ep.path.startswith("/") else f"/{ep.path}"
                if norm_path not in paths:
                    paths[norm_path] = {}

                method_key = ep.method.lower()

                # Build parameters
                parameters: list[dict[str, Any]] = []

                # Path variables
                path_var_names = set(re.findall(r"\{([a-zA-Z0-9_-]+)\}", norm_path))
                existing_param_names = set()

                if ep.request_params:
                    for p in ep.request_params:
                        existing_param_names.add(p.name)
                        param_in = p.param_type.lower()
                        param_obj: dict[str, Any] = {
                            "name": p.name,
                            "in": param_in,
                            "required": p.required or (param_in == "path"),
                            "schema": {"type": p.value_type or "string"},
                        }
                        if p.default_val is not None:
                            param_obj["schema"]["default"] = p.default_val
                        if p.description:
                            param_obj["description"] = p.description
                        parameters.append(param_obj)

                # Add any missing path parameters not explicitly listed in request_params
                for p_name in path_var_names:
                    if p_name not in existing_param_names:
                        parameters.append({
                            "name": p_name,
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": f"Path parameter {p_name}",
                        })

                # Build response
                status_code_str = str(ep.response_status)
                resp_content: dict[str, Any] = {}

                if ep.response_body_type == ResponseBodyType.JSON:
                    resp_content["application/json"] = {
                        "example": ep.response_body if ep.response_body is not None else {}
                    }
                elif ep.response_body_type == ResponseBodyType.TEXT:
                    resp_content["text/plain"] = {
                        "example": str(ep.response_body) if ep.response_body is not None else ""
                    }

                resp_obj: dict[str, Any] = {
                    "description": f"Mock response ({status_code_str}) for {ep.name}",
                }
                if resp_content:
                    resp_obj["content"] = resp_content

                if ep.response_headers:
                    resp_headers: dict[str, Any] = {}
                    for h in ep.response_headers:
                        resp_headers[h.name] = {
                            "schema": {"type": "string"},
                            "example": h.value,
                        }
                    resp_obj["headers"] = resp_headers

                operation: dict[str, Any] = {
                    "tags": [ctrl.name],
                    "summary": ep.name,
                    "description": ep.description or f"Mock endpoint for {ep.name}",
                    "operationId": f"{method_key}_{ctrl.name}_{ep.name}".replace(" ", "_").lower(),
                    "responses": {
                        status_code_str: resp_obj
                    },
                }

                if parameters:
                    operation["parameters"] = parameters

                # Request body
                if ep.method in ("POST", "PUT", "PATCH"):
                    body_schema = None
                    if ep.request_body and ep.request_body.schema_def:
                        body_schema = ep.request_body.schema_def
                    else:
                        body_schema = {"type": "object"}

                    operation["requestBody"] = {
                        "required": ep.request_body.required if ep.request_body else False,
                        "content": {
                            "application/json": {
                                "schema": body_schema,
                            }
                        },
                    }

                paths[norm_path][method_key] = operation

        # Security schemes
        components: dict[str, Any] = {}
        security: list[dict[str, list[str]]] = []

        if application.auth_config and application.auth_config.auth_type != "none":
            ac = application.auth_config
            if ac.auth_type == "bearer":
                components["securitySchemes"] = {
                    "BearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                    }
                }
                security.append({"BearerAuth": []})
            elif ac.auth_type == "api_key":
                header_name = ac.api_key_header or "X-API-Key"
                components["securitySchemes"] = {
                    "ApiKeyAuth": {
                        "type": "apiKey",
                        "in": "header",
                        "name": header_name,
                    }
                }
                security.append({"ApiKeyAuth": []})
            elif ac.auth_type == "basic":
                components["securitySchemes"] = {
                    "BasicAuth": {
                        "type": "http",
                        "scheme": "basic",
                    }
                }
                security.append({"BasicAuth": []})

        spec: dict[str, Any] = {
            "openapi": "3.0.3",
            "info": {
                "title": application.name,
                "version": "1.0.0",
                "description": application.description or f"Mock API specification for {application.name}",
            },
            "servers": [
                {
                    "url": f"/mock/{application.slug}",
                    "description": "MockEase Mock Server Base",
                }
            ],
            "tags": tags,
            "paths": paths,
        }

        if components:
            spec["components"] = components
        if security:
            spec["security"] = security

        return spec

    @staticmethod
    def export_to_postman(application: Application) -> dict[str, Any]:
        """Export an application into a Postman Collection v2.1 format."""
        controllers = [c for c in application.controllers if c.deleted_at is None]
        folders = []

        for ctrl in controllers:
            endpoints = [ep for ep in ctrl.endpoints if ep.deleted_at is None]
            items = []

            for ep in endpoints:
                norm_path = ep.path.strip("/")
                path_segments = norm_path.split("/") if norm_path else []

                headers = []
                if ep.response_headers:
                    for h in ep.response_headers:
                        headers.append({"key": h.name, "value": h.value, "type": "text"})

                query_params = []
                if ep.request_params:
                    for p in ep.request_params:
                        if p.param_type == ParamType.QUERY:
                            query_params.append({
                                "key": p.name,
                                "value": p.default_val or "",
                                "description": p.description or "",
                            })

                raw_body = ""
                if ep.response_body is not None:
                    if isinstance(ep.response_body, (dict, list)):
                        raw_body = json.dumps(ep.response_body, indent=2)
                    else:
                        raw_body = str(ep.response_body)

                req_obj: dict[str, Any] = {
                    "name": ep.name,
                    "request": {
                        "method": ep.method,
                        "header": headers,
                        "url": {
                            "raw": f"{{{{baseUrl}}}}/mock/{application.slug}/{norm_path}",
                            "host": ["{{baseUrl}}"],
                            "path": ["mock", application.slug, *path_segments],
                        },
                    },
                }

                if query_params:
                    req_obj["request"]["url"]["query"] = query_params

                if ep.method in ("POST", "PUT", "PATCH") and raw_body:
                    req_obj["request"]["body"] = {
                        "mode": "raw",
                        "raw": raw_body,
                        "options": {"raw": {"language": "json"}},
                    }

                # Sample response
                req_obj["response"] = [
                    {
                        "name": f"Mock {ep.response_status}",
                        "status": "OK" if ep.response_status == 200 else str(ep.response_status),
                        "code": ep.response_status,
                        "header": headers,
                        "body": raw_body,
                    }
                ]

                items.append(req_obj)

            folders.append({
                "name": ctrl.name,
                "description": ctrl.description or "",
                "item": items,
            })

        return {
            "info": {
                "_postman_id": str(application.id),
                "name": application.name,
                "description": application.description or f"MockEase Postman Collection for {application.name}",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            },
            "item": folders,
            "variable": [
                {
                    "key": "baseUrl",
                    "value": "http://localhost:8000",
                    "type": "string",
                }
            ],
        }

    @staticmethod
    def parse_spec_data(raw: str | dict[str, Any]) -> dict[str, Any]:
        """
        Parse raw OpenAPI (JSON or YAML) or Postman JSON into a standardized MockEase
        structure ready to persist into the database.
        """
        data: dict[str, Any]
        if isinstance(raw, str):
            trimmed = raw.strip()
            if trimmed.startswith("{") or trimmed.startswith("["):
                try:
                    data = json.loads(trimmed)
                except Exception:
                    data = yaml.safe_load(trimmed)
            else:
                data = yaml.safe_load(trimmed)
        else:
            data = raw

        if not isinstance(data, dict):
            raise ValueError("Invalid specification: Expected a JSON/YAML object")

        # Detect Postman collection vs OpenAPI / Swagger
        if "info" in data and "schema" in data["info"] and "postman" in data["info"]["schema"]:
            return OpenApiService._parse_postman(data)

        # Otherwise parse as OpenAPI 3.x or Swagger 2.0
        return OpenApiService._parse_openapi(data)

    @staticmethod
    def _parse_openapi(data: dict[str, Any]) -> dict[str, Any]:
        info = data.get("info", {})
        app_name = info.get("title", "Imported API")
        app_desc = info.get("description", "")

        paths = data.get("paths", {})
        if not isinstance(paths, dict):
            paths = {}

        controllers_map: dict[str, dict[str, Any]] = {}

        for path_str, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue

            for method_name, op in path_item.items():
                if method_name.upper() not in [m.value for m in HttpMethod]:
                    continue
                if not isinstance(op, dict):
                    continue

                method = method_name.upper()
                tags = op.get("tags", [])
                controller_name = tags[0] if tags and isinstance(tags, list) else "General"

                if controller_name not in controllers_map:
                    controllers_map[controller_name] = {
                        "name": controller_name,
                        "description": f"Endpoints for {controller_name}",
                        "endpoints": [],
                    }

                ep_name = op.get("summary") or op.get("operationId") or f"{method} {path_str}"
                ep_desc = op.get("description")

                # Parse parameters
                params_list = op.get("parameters", [])
                request_params = []
                for p in params_list:
                    if not isinstance(p, dict):
                        continue
                    p_in = p.get("in", "").lower()
                    if p_in in ("query", "path", "header"):
                        param_type = ParamType.QUERY
                        if p_in == "path":
                            param_type = ParamType.PATH
                        elif p_in == "header":
                            param_type = ParamType.HEADER

                        schema = p.get("schema", {})
                        v_type = schema.get("type", "string") if isinstance(schema, dict) else "string"
                        d_val = schema.get("default") if isinstance(schema, dict) else None

                        request_params.append({
                            "param_type": param_type,
                            "name": p.get("name", "param"),
                            "value_type": str(v_type),
                            "required": p.get("required", p_in == "path"),
                            "default_val": str(d_val) if d_val is not None else None,
                            "description": p.get("description"),
                        })

                # Parse response
                responses = op.get("responses", {})
                resp_status = 200
                resp_body: Any = None
                resp_body_type = ResponseBodyType.JSON

                if isinstance(responses, dict):
                    for code_key in ["200", "201", "204", "default", *responses.keys()]:
                        if code_key in responses:
                            try:
                                resp_status = int(code_key) if code_key.isdigit() else 200
                            except Exception:
                                resp_status = 200

                            resp_info = responses[code_key]
                            if isinstance(resp_info, dict):
                                content = resp_info.get("content", {})
                                if "application/json" in content:
                                    json_content = content["application/json"]
                                    if "example" in json_content:
                                        resp_body = json_content["example"]
                                    elif "schema" in json_content:
                                        resp_body = _generate_sample_from_schema(json_content["schema"])
                                    resp_body_type = ResponseBodyType.JSON
                                elif "text/plain" in content:
                                    resp_body = content["text/plain"].get("example", "OK")
                                    resp_body_type = ResponseBodyType.TEXT
                                # Swagger 2.0 response schema
                                elif "schema" in resp_info:
                                    resp_body = _generate_sample_from_schema(resp_info["schema"])
                                    resp_body_type = ResponseBodyType.JSON
                                elif "examples" in resp_info:
                                    for ex_val in resp_info["examples"].values():
                                        resp_body = ex_val
                                        break
                            break

                if resp_body is None:
                    resp_body = {"status": "ok", "message": f"Response from {ep_name}"}

                # Request body
                req_body = None
                if "requestBody" in op and isinstance(op["requestBody"], dict):
                    rb = op["requestBody"]
                    content = rb.get("content", {})
                    if "application/json" in content:
                        j_schema = content["application/json"].get("schema", {})
                        req_body = {
                            "body_type": RequestBodyType.JSON,
                            "schema_def": j_schema,
                            "required": rb.get("required", False),
                        }

                controllers_map[controller_name]["endpoints"].append({
                    "name": ep_name,
                    "description": ep_desc,
                    "method": method,
                    "path": path_str,
                    "response_status": resp_status,
                    "response_body": resp_body,
                    "response_body_type": resp_body_type,
                    "request_params": request_params,
                    "request_body": req_body,
                })

        return {
            "app_name": app_name,
            "description": app_desc,
            "controllers": list(controllers_map.values()),
        }

    @staticmethod
    def _parse_postman(data: dict[str, Any]) -> dict[str, Any]:
        info = data.get("info", {})
        app_name = info.get("name", "Imported Postman Collection")
        app_desc = info.get("description", "")

        controllers_map: dict[str, dict[str, Any]] = {}

        def process_items(items: list[Any], folder_name: str = "General") -> None:
            for item in items:
                if not isinstance(item, dict):
                    continue
                # If nested folder
                if "item" in item and isinstance(item["item"], list):
                    process_items(item["item"], item.get("name", folder_name))
                elif "request" in item and isinstance(item["request"], dict):
                    req = item["request"]
                    method = req.get("method", "GET").upper()
                    if method not in [m.value for m in HttpMethod]:
                        method = "GET"

                    ctrl_name = folder_name or "General"
                    if ctrl_name not in controllers_map:
                        controllers_map[ctrl_name] = {
                            "name": ctrl_name,
                            "description": f"Endpoints under {ctrl_name}",
                            "endpoints": [],
                        }

                    # Parse URL
                    url_obj = req.get("url", {})
                    path_str = "/"
                    query_params = []

                    if isinstance(url_obj, str):
                        match = re.search(r"https?://[^/]+(/.*)", url_obj)
                        path_str = match.group(1) if match else url_obj
                        if not path_str.startswith("/"):
                            path_str = f"/{path_str}"
                    elif isinstance(url_obj, dict):
                        paths_list = url_obj.get("path", [])
                        if isinstance(paths_list, list):
                            # Remove initial 'mock' and slug if exported from MockEase
                            clean_segments = []
                            for seg in paths_list:
                                if seg not in ("mock",):
                                    clean_segments.append(seg)
                            # Remove first segment if it looks like app slug
                            path_str = "/" + "/".join(clean_segments)
                        if "query" in url_obj and isinstance(url_obj["query"], list):
                            for q in url_obj["query"]:
                                if isinstance(q, dict) and "key" in q:
                                    query_params.append({
                                        "param_type": ParamType.QUERY,
                                        "name": q["key"],
                                        "value_type": "string",
                                        "required": False,
                                        "default_val": q.get("value"),
                                        "description": q.get("description"),
                                    })

                    # Parse body
                    resp_body: Any = {"status": "ok"}
                    resp_status = 200

                    responses = item.get("response", [])
                    if responses and isinstance(responses, list) and isinstance(responses[0], dict):
                        first_res = responses[0]
                        resp_status = first_res.get("code", 200)
                        raw_body = first_res.get("body", "")
                        if raw_body:
                            try:
                                resp_body = json.loads(raw_body)
                            except Exception:
                                resp_body = raw_body

                    controllers_map[ctrl_name]["endpoints"].append({
                        "name": item.get("name", f"{method} {path_str}"),
                        "description": req.get("description"),
                        "method": method,
                        "path": path_str,
                        "response_status": resp_status,
                        "response_body": resp_body,
                        "response_body_type": ResponseBodyType.JSON if isinstance(resp_body, (dict, list)) else ResponseBodyType.TEXT,
                        "request_params": query_params,
                        "request_body": None,
                    })

        raw_items = data.get("item", [])
        if isinstance(raw_items, list):
            process_items(raw_items)

        return {
            "app_name": app_name,
            "description": app_desc,
            "controllers": list(controllers_map.values()),
        }

    @staticmethod
    async def create_application_from_spec(
        db: AsyncSession,
        user_id: uuid.UUID,
        parsed_data: dict[str, Any],
        override_name: str | None = None,
    ) -> Application:
        """Create a new Application and its Controllers & Endpoints from parsed spec data."""
        name = (override_name or parsed_data.get("app_name") or "Imported API").strip()
        slug = unique_slug(name)

        app = Application(
            user_id=user_id,
            name=name[:255],
            slug=slug,
            description=parsed_data.get("description"),
            is_enabled=True,
        )
        db.add(app)
        await db.flush()

        pos = 0
        for ctrl_data in parsed_data.get("controllers", []):
            ctrl = Controller(
                application_id=app.id,
                name=ctrl_data["name"][:255],
                description=ctrl_data.get("description"),
                is_enabled=True,
                position=pos,
            )
            db.add(ctrl)
            await db.flush()
            pos += 1

            for ep_data in ctrl_data.get("endpoints", []):
                clean_path = ep_data["path"].strip()
                if not clean_path.startswith("/"):
                    clean_path = "/" + clean_path

                method_str = ep_data["method"].upper()
                method_enum = (
                    HttpMethod(method_str)
                    if method_str in [m.value for m in HttpMethod]
                    else HttpMethod.GET
                )

                ep = ApiEndpoint(
                    controller_id=ctrl.id,
                    name=ep_data["name"][:255],
                    description=ep_data.get("description"),
                    method=method_enum,
                    path=clean_path,
                    response_status=ep_data.get("response_status", 200),
                    response_body=ep_data.get("response_body"),
                    response_body_type=ep_data.get("response_body_type", ResponseBodyType.JSON),
                    response_delay_ms=0,
                    is_enabled=True,
                )
                db.add(ep)
                await db.flush()

                for param in ep_data.get("request_params", []):
                    db.add(
                        ApiRequestParam(
                            endpoint_id=ep.id,
                            param_type=param["param_type"],
                            name=param["name"][:255],
                            value_type=param.get("value_type", "string"),
                            required=param.get("required", False),
                            default_val=param.get("default_val"),
                            description=param.get("description"),
                        )
                    )

                req_b = ep_data.get("request_body")
                if req_b:
                    db.add(
                        ApiRequestBody(
                            endpoint_id=ep.id,
                            body_type=req_b.get("body_type", RequestBodyType.JSON),
                            schema_def=req_b.get("schema_def"),
                            required=req_b.get("required", False),
                        )
                    )

        await db.flush()
        return app

    @staticmethod
    async def merge_spec_into_application(
        db: AsyncSession,
        app: Application,
        parsed_data: dict[str, Any],
    ) -> None:
        """Merge Controllers and Endpoints from parsed spec data into an existing Application."""
        existing_controllers_query = (
            select(Controller)
            .where(Controller.application_id == app.id, Controller.deleted_at.is_(None))
            .options(selectinload(Controller.endpoints))
        )
        res = await db.execute(existing_controllers_query)
        existing_ctrls = res.scalars().all()
        ctrl_map = {c.name.strip().lower(): c for c in existing_ctrls}

        pos = len(existing_ctrls)
        for ctrl_data in parsed_data.get("controllers", []):
            ctrl_name_key = ctrl_data["name"].strip().lower()
            if ctrl_name_key in ctrl_map:
                ctrl = ctrl_map[ctrl_name_key]
            else:
                ctrl = Controller(
                    application_id=app.id,
                    name=ctrl_data["name"][:255],
                    description=ctrl_data.get("description"),
                    is_enabled=True,
                    position=pos,
                )
                db.add(ctrl)
                await db.flush()
                ctrl_map[ctrl_name_key] = ctrl
                pos += 1

            existing_eps_query = select(ApiEndpoint).where(
                ApiEndpoint.controller_id == ctrl.id, ApiEndpoint.deleted_at.is_(None)
            )
            ep_res = await db.execute(existing_eps_query)
            existing_eps = ep_res.scalars().all()
            ep_set = {(e.method.value, e.path.rstrip("/")) for e in existing_eps}

            for ep_data in ctrl_data.get("endpoints", []):
                clean_path = ep_data["path"].strip()
                if not clean_path.startswith("/"):
                    clean_path = "/" + clean_path

                method_str = ep_data["method"].upper()
                method_enum = (
                    HttpMethod(method_str)
                    if method_str in [m.value for m in HttpMethod]
                    else HttpMethod.GET
                )

                if (method_enum.value, clean_path.rstrip("/")) in ep_set:
                    continue

                ep = ApiEndpoint(
                    controller_id=ctrl.id,
                    name=ep_data["name"][:255],
                    description=ep_data.get("description"),
                    method=method_enum,
                    path=clean_path,
                    response_status=ep_data.get("response_status", 200),
                    response_body=ep_data.get("response_body"),
                    response_body_type=ep_data.get("response_body_type", ResponseBodyType.JSON),
                    response_delay_ms=0,
                    is_enabled=True,
                )
                db.add(ep)
                await db.flush()
                ep_set.add((method_enum.value, clean_path.rstrip("/")))

                for param in ep_data.get("request_params", []):
                    db.add(
                        ApiRequestParam(
                            endpoint_id=ep.id,
                            param_type=param["param_type"],
                            name=param["name"][:255],
                            value_type=param.get("value_type", "string"),
                            required=param.get("required", False),
                            default_val=param.get("default_val"),
                            description=param.get("description"),
                        )
                    )

                req_b = ep_data.get("request_body")
                if req_b:
                    db.add(
                        ApiRequestBody(
                            endpoint_id=ep.id,
                            body_type=req_b.get("body_type", RequestBodyType.JSON),
                            schema_def=req_b.get("schema_def"),
                            required=req_b.get("required", False),
                        )
                    )

        await db.flush()

