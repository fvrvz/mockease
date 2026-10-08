"""initial_schema

Revision ID: 17d14cb3ff52
Revises:
Create Date: 2026-10-08 13:15:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "17d14cb3ff52"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enum columns will create types automatically if needed.

    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("username", sa.String(100), nullable=False),
        sa.Column("password_hash", sa.Text, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    # --- applications ---
    op.create_table(
        "applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("is_enabled", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_applications_slug", "applications", ["slug"], unique=True)
    op.create_index("ix_applications_user_id", "applications", ["user_id"])

    # --- controllers ---
    op.create_table(
        "controllers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("applications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("is_enabled", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("position", sa.Integer, nullable=False, server_default="0"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_controllers_application_id", "controllers", ["application_id"])

    # --- api_endpoints ---
    op.create_table(
        "api_endpoints",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("controller_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("controllers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("method", sa.Enum("GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS", name="http_method", create_type=False), nullable=False),
        sa.Column("path", sa.String(1000), nullable=False),
        sa.Column("is_enabled", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("auth_inherit", sa.Enum("inherit", "override_on", "override_off", name="auth_inherit", create_type=False), nullable=False, server_default="inherit"),
        sa.Column("response_status", sa.Integer, nullable=False, server_default="200"),
        sa.Column("response_body", postgresql.JSONB, nullable=True),
        sa.Column("response_body_type", sa.Enum("json", "text", "empty", name="response_body_type", create_type=False), nullable=False, server_default="json"),
        sa.Column("response_delay_ms", sa.Integer, nullable=False, server_default="0"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_api_endpoints_controller_id", "api_endpoints", ["controller_id"])
    op.create_index("ix_api_endpoints_method_path", "api_endpoints", ["method", "path"])

    # --- api_request_params ---
    op.create_table(
        "api_request_params",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("endpoint_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("api_endpoints.id", ondelete="CASCADE"), nullable=False),
        sa.Column("param_type", sa.Enum("query", "path", "header", name="param_type", create_type=False), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("value_type", sa.String(50), nullable=False, server_default="string"),
        sa.Column("required", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("default_val", sa.Text, nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_api_request_params_endpoint_id", "api_request_params", ["endpoint_id"])

    # --- api_request_bodies ---
    op.create_table(
        "api_request_bodies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("endpoint_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("api_endpoints.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("body_type", sa.Enum("json", "form", "urlencoded", "raw", "none", name="request_body_type", create_type=False), nullable=False, server_default="none"),
        sa.Column("schema", postgresql.JSONB, nullable=True),
        sa.Column("required", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # --- api_response_headers ---
    op.create_table(
        "api_response_headers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("endpoint_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("api_endpoints.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("value", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_api_response_headers_endpoint_id", "api_response_headers", ["endpoint_id"])

    # --- auth_configs ---
    op.create_table(
        "auth_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("auth_type", sa.Enum("none", "api_key", "bearer", "basic", name="auth_type", create_type=False), nullable=False, server_default="none"),
        sa.Column("api_key_header", sa.String(255), nullable=True),
        sa.Column("api_key_value", sa.Text, nullable=True),
        sa.Column("bearer_token", sa.Text, nullable=True),
        sa.Column("basic_username", sa.String(255), nullable=True),
        sa.Column("basic_password", sa.Text, nullable=True),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("applications.id", ondelete="CASCADE"), nullable=True),
        sa.Column("controller_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("controllers.id", ondelete="CASCADE"), nullable=True),
        sa.Column("endpoint_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("api_endpoints.id", ondelete="CASCADE"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_auth_configs_application_id", "auth_configs", ["application_id"])
    op.create_index("ix_auth_configs_controller_id", "auth_configs", ["controller_id"])
    op.create_index("ix_auth_configs_endpoint_id", "auth_configs", ["endpoint_id"])


def downgrade() -> None:
    op.drop_table("auth_configs")
    op.drop_table("api_response_headers")
    op.drop_table("api_request_bodies")
    op.drop_table("api_request_params")
    op.drop_table("api_endpoints")
    op.drop_table("controllers")
    op.drop_table("applications")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS request_body_type")
    op.execute("DROP TYPE IF EXISTS param_type")
    op.execute("DROP TYPE IF EXISTS response_body_type")
    op.execute("DROP TYPE IF EXISTS auth_inherit")
    op.execute("DROP TYPE IF EXISTS http_method")
    op.execute("DROP TYPE IF EXISTS auth_type")
