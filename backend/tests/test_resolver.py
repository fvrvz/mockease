from __future__ import annotations

import uuid
from src.mock_runtime.resolver import match_endpoint, normalize_path
from src.models.endpoint import ApiEndpoint, HttpMethod


def test_normalize_path():
    assert normalize_path("users/list") == "/users/list"
    assert normalize_path("/users/list/") == "/users/list"
    assert normalize_path("") == "/"


def test_match_static_endpoint():
    ep = ApiEndpoint(
        id=uuid.uuid4(),
        controller_id=uuid.uuid4(),
        name="Get Users",
        method=HttpMethod.GET,
        path="/users",
    )
    matched, params = match_endpoint("GET", "/users", [ep])
    assert matched is ep
    assert params == {}


def test_match_dynamic_endpoint_brace_syntax():
    ep = ApiEndpoint(
        id=uuid.uuid4(),
        controller_id=uuid.uuid4(),
        name="Get User by ID",
        method=HttpMethod.GET,
        path="/users/{id}",
    )
    matched, params = match_endpoint("GET", "/users/123", [ep])
    assert matched is ep
    assert params == {"id": "123"}


def test_match_dynamic_endpoint_colon_syntax():
    ep = ApiEndpoint(
        id=uuid.uuid4(),
        controller_id=uuid.uuid4(),
        name="Get User by ID",
        method=HttpMethod.GET,
        path="/users/:id/posts/:post_id",
    )
    matched, params = match_endpoint("GET", "/users/42/posts/99", [ep])
    assert matched is ep
    assert params == {"id": "42", "post_id": "99"}


def test_no_match():
    ep = ApiEndpoint(
        id=uuid.uuid4(),
        controller_id=uuid.uuid4(),
        name="Get Users",
        method=HttpMethod.GET,
        path="/users",
    )
    matched, params = match_endpoint("POST", "/users", [ep])
    assert matched is None
    assert params == {}
