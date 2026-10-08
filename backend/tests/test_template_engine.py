from __future__ import annotations

import uuid
from src.mock_runtime.template_engine import render_template


def test_render_uuid():
    rendered = render_template("ID: {{uuid}}", {})
    assert rendered.startswith("ID: ")
    val = rendered.replace("ID: ", "").strip()
    uuid.UUID(val)  # Validates valid UUID


def test_render_timestamp():
    rendered = render_template("Time: {{timestamp}}", {})
    assert rendered.startswith("Time: ")
    num_str = rendered.replace("Time: ", "").strip()
    assert num_str.isdigit()


def test_render_random_helpers():
    rendered_name = render_template("{{random.name}}", {})
    assert len(rendered_name) > 0
    assert "{{" not in rendered_name

    rendered_email = render_template("{{random.email}}", {})
    assert "@" in rendered_email

    rendered_num = render_template("{{random.number}}", {})
    assert isinstance(rendered_num, int) or (isinstance(rendered_num, str) and rendered_num.isdigit())


def test_render_context_request():
    context = {
        "request": {
            "query": {"page": "2", "limit": "50"},
            "path": {"id": "user_abc"},
            "header": {"authorization": "Bearer token123"},
        }
    }

    template_dict = {
        "userId": "{{request.path.id}}",
        "currentPage": "{{request.query.page}}",
        "pageSize": "{{request.query.limit}}",
    }

    result = render_template(template_dict, context)
    assert result == {
        "userId": "user_abc",
        "currentPage": "2",
        "pageSize": "50",
    }
