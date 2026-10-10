from __future__ import annotations

import base64
import pytest
from src.models.auth_config import AuthConfig, AuthType
from src.mock_runtime.auth_validator import validate_auth
from src.utils.slugify import slugify, unique_slug
from src.utils.response import success, error


def test_auth_validator_none() -> None:
    config = AuthConfig(auth_type=AuthType.NONE)
    result = validate_auth(config, {})
    assert result.is_valid is True

    result_none = validate_auth(None, {})
    assert result_none.is_valid is True


def test_auth_validator_api_key() -> None:
    config = AuthConfig(
        auth_type=AuthType.API_KEY,
        api_key_header="X-API-Key",
        api_key_value="secret-val",
    )
    # Missing header
    res1 = validate_auth(config, {})
    assert res1.is_valid is False
    assert res1.status_code == 401

    # Wrong value
    res2 = validate_auth(config, {"X-API-Key": "wrong"})
    assert res2.is_valid is False
    assert res2.status_code == 403

    # Valid
    res3 = validate_auth(config, {"X-API-Key": "secret-val"})
    assert res3.is_valid is True


def test_auth_validator_bearer() -> None:
    config = AuthConfig(
        auth_type=AuthType.BEARER,
        bearer_token="my-token",
    )
    # Missing
    res1 = validate_auth(config, {})
    assert res1.is_valid is False
    assert res1.status_code == 401

    # Malformed
    res2 = validate_auth(config, {"authorization": "Token my-token"})
    assert res2.is_valid is False

    # Wrong token
    res3 = validate_auth(config, {"authorization": "Bearer wrong"})
    assert res3.is_valid is False
    assert res3.status_code == 403

    # Valid
    res4 = validate_auth(config, {"authorization": "Bearer my-token"})
    assert res4.is_valid is True


def test_auth_validator_basic() -> None:
    config = AuthConfig(
        auth_type=AuthType.BASIC,
        basic_username="admin",
        basic_password="password",
    )
    # Missing
    res1 = validate_auth(config, {})
    assert res1.is_valid is False

    # Malformed base64
    res2 = validate_auth(config, {"authorization": "Basic not-base64!!!"})
    assert res2.is_valid is False

    # Invalid credential string (no colon)
    bad_cred = base64.b64encode(b"no-colon").decode("utf-8")
    res3 = validate_auth(config, {"authorization": f"Basic {bad_cred}"})
    assert res3.is_valid is False

    # Wrong user
    wrong_user = base64.b64encode(b"wrong:password").decode("utf-8")
    res4 = validate_auth(config, {"authorization": f"Basic {wrong_user}"})
    assert res4.is_valid is False

    # Wrong password
    wrong_pwd = base64.b64encode(b"admin:wrong").decode("utf-8")
    res5 = validate_auth(config, {"authorization": f"Basic {wrong_pwd}"})
    assert res5.is_valid is False

    # Valid
    valid_cred = base64.b64encode(b"admin:password").decode("utf-8")
    res6 = validate_auth(config, {"authorization": f"Basic {valid_cred}"})
    assert res6.is_valid is True


def test_slugify_and_unique_slug() -> None:
    assert slugify("Hello World!") == "hello-world"
    assert slugify("  Mock   API --- Test  ") == "mock-api-test"
    assert slugify("###Special@Chars###") == "specialchars"

    u1 = unique_slug("app")
    u2 = unique_slug("app")
    assert u1.startswith("app-")
    assert u2.startswith("app-")
    assert u1 != u2


def test_response_helpers() -> None:
    s = success(data={"val": 123}, message="Success message", status_code=200)
    assert s.status_code == 200

    e = error(code="NOT_FOUND", message="Resource missing", status_code=404, details={"id": 1})
    assert e.status_code == 404
