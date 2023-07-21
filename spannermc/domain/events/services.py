from __future__ import annotations

from typing import Any

from litestar.contrib.sqlalchemy.repository import SQLAlchemySyncRepository

from spannermc.lib.service.sqlalchemy import SQLAlchemySyncRepositoryService

from .models import Event

__all__ = ["EventService", "EventRepository"]


class EventRepository(SQLAlchemySyncRepository[Event]):
    """Event SQLAlchemy Repository."""

    model_type = Event


class EventService(SQLAlchemySyncRepositoryService[Event]):
    """Handles database operations for users."""

    repository_type = EventRepository

    def __init__(self, **repo_kwargs: Any) -> None:
        self.repository: EventRepository = self.repository_type(**repo_kwargs)
        self.model_type = self.repository.model_type
