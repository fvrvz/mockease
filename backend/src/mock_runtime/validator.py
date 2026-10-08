from __future__ import annotations

from typing import Any
from src.models.endpoint import ApiRequestParam, ApiRequestBody, ParamType, RequestBodyType


class ValidationResult:
    def __init__(self, is_valid: bool, error_message: str | None = None, status_code: int = 400):
        self.is_valid = is_valid
        self.error_message = error_message
        self.status_code = status_code


def validate_request_params(
    params: list[ApiRequestParam],
    query_params: dict[str, str],
    headers: dict[str, str],
) -> ValidationResult:
    lower_headers = {k.lower(): v for k, v in headers.items()}

    for param in params:
        if param.param_type == ParamType.QUERY:
            val = query_params.get(param.name)
            if param.required and (val is None or val == ""):
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Missing required query parameter '{param.name}'",
                    status_code=400,
                )
        elif param.param_type == ParamType.HEADER:
            val = lower_headers.get(param.name.lower())
            if param.required and (val is None or val == ""):
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Missing required header '{param.name}'",
                    status_code=400,
                )

    return ValidationResult(is_valid=True)


def validate_request_body(
    request_body_def: ApiRequestBody | None,
    raw_body: bytes,
    parsed_json: Any | None,
) -> ValidationResult:
    if not request_body_def or request_body_def.body_type == RequestBodyType.NONE:
        return ValidationResult(is_valid=True)

    has_body = bool(raw_body and len(raw_body.strip()) > 0)

    if request_body_def.required and not has_body:
        return ValidationResult(
            is_valid=False,
            error_message="Request body is required but was empty",
            status_code=400,
        )

    if request_body_def.body_type == RequestBodyType.JSON and has_body:
        if parsed_json is None:
            return ValidationResult(
                is_valid=False,
                error_message="Invalid JSON payload provided in request body",
                status_code=400,
            )

    return ValidationResult(is_valid=True)
