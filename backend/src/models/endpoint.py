from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from src.db.base import Base


class HttpMethod(str, enum.Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class AuthInherit(str, enum.Enum):
    INHERIT = "inherit"
    OVERRIDE_ON = "override_on"
    OVERRIDE_OFF = "override_off"


class ResponseBodyType(str, enum.Enum):
    JSON = "json"
    TEXT = "text"
    EMPTY = "empty"


class ParamType(str, enum.Enum):
    QUERY = "query"
    PATH = "path"
    HEADER = "header"


class RequestBodyType(str, enum.Enum):
    JSON = "json"
    FORM = "form"
    URLENCODED = "urlencoded"
    RAW = "raw"
    NONE = "none"


class ApiEndpoint(Base):
    __tablename__ = "api_endpoints"

    controller_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("controllers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    method: Mapped[HttpMethod] = mapped_column(
        Enum(HttpMethod, name="http_method"), nullable=False
    )
    path: Mapped[str] = mapped_column(String(1000), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    auth_inherit: Mapped[AuthInherit] = mapped_column(
        Enum(AuthInherit, name="auth_inherit"), default=AuthInherit.INHERIT, nullable=False
    )
    response_status: Mapped[int] = mapped_column(Integer, default=200, nullable=False)
    response_body: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    response_body_type: Mapped[ResponseBodyType] = mapped_column(
        Enum(ResponseBodyType, name="response_body_type"),
        default=ResponseBodyType.JSON,
        nullable=False,
    )
    response_delay_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    controller: Mapped["Controller"] = relationship("Controller", back_populates="endpoints")
    request_params: Mapped[list["ApiRequestParam"]] = relationship(
        "ApiRequestParam", back_populates="endpoint", cascade="all, delete-orphan"
    )
    request_body: Mapped["ApiRequestBody | None"] = relationship(
        "ApiRequestBody", back_populates="endpoint", uselist=False, cascade="all, delete-orphan"
    )
    response_headers: Mapped[list["ApiResponseHeader"]] = relationship(
        "ApiResponseHeader", back_populates="endpoint", cascade="all, delete-orphan"
    )
    auth_config: Mapped["AuthConfig | None"] = relationship(
        "AuthConfig",
        foreign_keys="AuthConfig.endpoint_id",
        uselist=False,
        lazy="select",
    )


class ApiRequestParam(Base):
    __tablename__ = "api_request_params"

    endpoint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("api_endpoints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    param_type: Mapped[ParamType] = mapped_column(
        Enum(ParamType, name="param_type"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    value_type: Mapped[str] = mapped_column(String(50), default="string", nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    default_val: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    endpoint: Mapped[ApiEndpoint] = relationship("ApiEndpoint", back_populates="request_params")


class ApiRequestBody(Base):
    __tablename__ = "api_request_bodies"

    endpoint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("api_endpoints.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    body_type: Mapped[RequestBodyType] = mapped_column(
        Enum(RequestBodyType, name="request_body_type"),
        default=RequestBodyType.NONE,
        nullable=False,
    )
    schema_def: Mapped[dict | None] = mapped_column("schema", JSONB, nullable=True)
    required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    endpoint: Mapped[ApiEndpoint] = relationship("ApiEndpoint", back_populates="request_body")


class ApiResponseHeader(Base):
    __tablename__ = "api_response_headers"

    endpoint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("api_endpoints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)

    endpoint: Mapped[ApiEndpoint] = relationship("ApiEndpoint", back_populates="response_headers")
