from __future__ import annotations

import uuid
from src.mock_runtime.validator import validate_request_params, validate_request_body
from src.models.endpoint import ApiRequestParam, ApiRequestBody, ParamType, RequestBodyType


def test_validate_required_query_param():
    param = ApiRequestParam(
        endpoint_id=uuid.uuid4(),
        param_type=ParamType.QUERY,
        name="page",
        required=True,
    )

    # Missing param
    res1 = validate_request_params([param], {}, {})
    assert not res1.is_valid
    assert "Missing required query parameter" in res1.error_message

    # Present param
    res2 = validate_request_params([param], {"page": "1"}, {})
    assert res2.is_valid


def test_validate_required_header_param():
    param = ApiRequestParam(
        endpoint_id=uuid.uuid4(),
        param_type=ParamType.HEADER,
        name="X-Tenant-ID",
        required=True,
    )

    # Missing header
    res1 = validate_request_params([param], {}, {})
    assert not res1.is_valid
    assert "Missing required header" in res1.error_message

    # Case-insensitive header match
    res2 = validate_request_params([param], {}, {"x-tenant-id": "tenant-99"})
    assert res2.is_valid


def test_validate_request_body():
    body_def = ApiRequestBody(
        endpoint_id=uuid.uuid4(),
        body_type=RequestBodyType.JSON,
        required=True,
    )

    # Empty body when required
    res1 = validate_request_body(body_def, b"", None)
    assert not res1.is_valid
    assert "Request body is required" in res1.error_message

    # Malformed JSON
    res2 = validate_request_body(body_def, b"{bad json}", None)
    assert not res2.is_valid
    assert "Invalid JSON payload" in res2.error_message

    # Valid JSON
    res3 = validate_request_body(body_def, b'{"name": "Alice"}', {"name": "Alice"})
    assert res3.is_valid
