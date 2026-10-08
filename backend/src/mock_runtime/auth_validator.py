from __future__ import annotations

import base64
from typing import Any

from src.models.auth_config import AuthConfig, AuthType


class AuthValidationResult:
    def __init__(self, is_valid: bool, error_message: str | None = None, status_code: int = 401):
        self.is_valid = is_valid
        self.error_message = error_message
        self.status_code = status_code


def validate_auth(
    auth_config: AuthConfig | None,
    headers: dict[str, str],
) -> AuthValidationResult:
    if not auth_config or auth_config.auth_type == AuthType.NONE:
        return AuthValidationResult(is_valid=True)

    lower_headers = {k.lower(): v for k, v in headers.items()}

    if auth_config.auth_type == AuthType.API_KEY:
        header_name = (auth_config.api_key_header or "x-api-key").lower()
        provided = lower_headers.get(header_name)
        if not provided:
            return AuthValidationResult(
                is_valid=False,
                error_message=f"Missing API key header '{auth_config.api_key_header or 'X-API-Key'}'",
                status_code=401,
            )
        if auth_config.api_key_value and provided != auth_config.api_key_value:
            return AuthValidationResult(
                is_valid=False,
                error_message="Invalid API key",
                status_code=403,
            )
        return AuthValidationResult(is_valid=True)

    elif auth_config.auth_type == AuthType.BEARER:
        auth_header = lower_headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return AuthValidationResult(
                is_valid=False,
                error_message="Missing or malformed Authorization header (expected Bearer token)",
                status_code=401,
            )
        token = auth_header[7:].strip()
        if auth_config.bearer_token and token != auth_config.bearer_token:
            return AuthValidationResult(
                is_valid=False,
                error_message="Invalid Bearer token",
                status_code=403,
            )
        return AuthValidationResult(is_valid=True)

    elif auth_config.auth_type == AuthType.BASIC:
        auth_header = lower_headers.get("authorization", "")
        if not auth_header.startswith("Basic "):
            return AuthValidationResult(
                is_valid=False,
                error_message="Missing or malformed Authorization header (expected Basic auth)",
                status_code=401,
            )
        try:
            encoded = auth_header[6:].strip()
            decoded = base64.b64decode(encoded).decode("utf-8")
            if ":" not in decoded:
                return AuthValidationResult(
                    is_valid=False,
                    error_message="Malformed Basic auth credentials",
                    status_code=401,
                )
            username, password = decoded.split(":", 1)
        except Exception:
            return AuthValidationResult(
                is_valid=False,
                error_message="Unable to decode Basic auth credentials",
                status_code=401,
            )

        if auth_config.basic_username and username != auth_config.basic_username:
            return AuthValidationResult(
                is_valid=False,
                error_message="Invalid Basic auth credentials",
                status_code=401,
            )
        if auth_config.basic_password and password != auth_config.basic_password:
            return AuthValidationResult(
                is_valid=False,
                error_message="Invalid Basic auth credentials",
                status_code=401,
            )
        return AuthValidationResult(is_valid=True)

    return AuthValidationResult(is_valid=True)
