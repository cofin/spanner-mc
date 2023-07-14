from __future__ import annotations

from datetime import datetime  # noqa: TCH003
from typing import TYPE_CHECKING

from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from spannermc.lib import dto
from spannermc.lib.db import orm

if TYPE_CHECKING:
    from spannermc.domain.events.models import Event

__all__ = ["User"]


class User(orm.TimestampedDatabaseModel):
    """User Model."""

    __tablename__ = "user_account"  # type: ignore[assignment]
    __table_args__ = (
        Index("uk_user_account_email", "email", unique=True),
        {"comment": "User accounts for application access"},
    )
    email: Mapped[str]
    name: Mapped[str | None]
    hashed_password: Mapped[str | None] = mapped_column(String(length=255), info=dto.dto_field("private"))
    is_active: Mapped[bool] = mapped_column(default=True)
    is_superuser: Mapped[bool] = mapped_column(default=False)
    is_verified: Mapped[bool] = mapped_column(default=False)
    verified_at: Mapped[datetime | None] = mapped_column(info=dto.dto_field("read-only"))
    # -----------
    # ORM Relationships
    # ------------
    events: Mapped[list[Event]] = relationship(
        back_populates="user",
        lazy="noload",
        uselist=True,
        cascade="all, delete",
        viewonly=True,
    )
