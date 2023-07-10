from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID  # noqa: TCH003

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from spannermc.lib.db import orm

if TYPE_CHECKING:
    from spannermc.domain.accounts.models import User

__all__ = ["Event"]


class Event(orm.TimestampedDatabaseModel):
    """Event Model."""

    __tablename__ = "event"  # type: ignore[assignment]
    __table_args__ = ({"comment": "Events"},)
    message: Mapped[str]
    user_id: Mapped[UUID] = mapped_column(ForeignKey("user_account.id"))

    # -----------
    # ORM Relationships
    # ------------
    user: Mapped[User] = relationship(
        back_populates="events", foreign_keys="Event.user_id", innerjoin=True, uselist=False, lazy="joined"
    )
