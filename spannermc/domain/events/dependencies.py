"""Event deps."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from spannermc.domain.events.models import Event
from spannermc.domain.events.services import EventService
from spannermc.lib import log

if TYPE_CHECKING:
    from collections.abc import Generator

    from sqlalchemy.orm import Session

__all__ = ["provides_event_service"]


logger = log.get_logger()


def provides_event_service(db_session: Session) -> Generator[EventService, None, None]:
    """Construct repository and service objects for the request."""
    with EventService.new(
        session=db_session,
        statement=select(Event).order_by(Event.created_at),
    ) as service:
        yield service
