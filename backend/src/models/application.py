from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base


class Application(Base):
    __tablename__ = "applications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="applications")
    controllers: Mapped[list["Controller"]] = relationship(
        "Controller", back_populates="application", lazy="select"
    )
    auth_config: Mapped["AuthConfig | None"] = relationship(
        "AuthConfig",
        primaryjoin="and_(AuthConfig.application_id == Application.id, AuthConfig.controller_id == None, AuthConfig.endpoint_id == None)",
        foreign_keys="AuthConfig.application_id",
        uselist=False,
        lazy="select",
    )
