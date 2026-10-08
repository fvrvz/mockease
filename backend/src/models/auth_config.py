from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


class AuthType(str, enum.Enum):
    NONE = "none"
    API_KEY = "api_key"
    BEARER = "bearer"
    BASIC = "basic"


class AuthConfig(Base):
    __tablename__ = "auth_configs"

    auth_type: Mapped[AuthType] = mapped_column(
        Enum(AuthType, name="auth_type", values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=AuthType.NONE
    )

    # API Key
    api_key_header: Mapped[str | None] = mapped_column(String(255), nullable=True)
    api_key_value: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Bearer
    bearer_token: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Basic
    basic_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    basic_password: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Polymorphic owner FKs (exactly one will be set)
    application_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=True, index=True
    )
    controller_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("controllers.id", ondelete="CASCADE"), nullable=True, index=True
    )
    endpoint_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("api_endpoints.id", ondelete="CASCADE"), nullable=True, index=True
    )
