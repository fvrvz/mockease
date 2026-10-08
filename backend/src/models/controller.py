from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base


class Controller(Base):
    __tablename__ = "controllers"

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    application: Mapped["Application"] = relationship("Application", back_populates="controllers")
    endpoints: Mapped[list["ApiEndpoint"]] = relationship(
        "ApiEndpoint", back_populates="controller", lazy="select"
    )
    auth_config: Mapped["AuthConfig | None"] = relationship(
        "AuthConfig",
        primaryjoin="and_(AuthConfig.controller_id == Controller.id, AuthConfig.endpoint_id == None)",
        foreign_keys="AuthConfig.controller_id",
        uselist=False,
        lazy="select",
    )
