"""Event Controllers."""
from __future__ import annotations

from typing import TYPE_CHECKING

from litestar import Controller, delete, get, patch, post
from litestar.di import Provide
from litestar.params import Dependency, Parameter

from spannermc.domain import urls
from spannermc.domain.accounts.models import User
from spannermc.domain.events.dependencies import provides_event_service
from spannermc.domain.events.dtos import EventDTO, EventModifyDTO
from spannermc.domain.events.guards import requires_event_ownership
from spannermc.domain.events.models import Event
from spannermc.domain.events.services import EventService
from spannermc.lib import log

__all__ = ["EventController"]


if TYPE_CHECKING:
    from uuid import UUID

    from litestar.contrib.repository.filters import FilterTypes
    from litestar.dto import DTOData
    from litestar.pagination import OffsetPagination


logger = log.get_logger()


class EventController(Controller):
    """Event Controller."""

    tags = ["Event"]
    dependencies = {"events_service": Provide(provides_event_service)}
    signature_namespace = {"EventService": EventService, "User": User, "Event": Event}
    return_dto = EventDTO

    @get(
        operation_id="ListEvents",
        name="events:list",
        summary="List Events",
        description="Retrieve the events.",
        path=urls.EVENT_LIST,
        sync_to_thread=False,
    )
    def list_events(
        self, events_service: EventService, filters: list[FilterTypes] = Dependency(skip_validation=True)
    ) -> OffsetPagination[Event]:
        """List events."""
        results, total = events_service.list_and_count(*filters)
        return events_service.to_dto(results, total, *filters)

    @get(
        operation_id="GetEvent",
        name="events:get",
        path=urls.EVENT_DETAIL,
        summary="Retrieve the details of a event.",
        sync_to_thread=False,
    )
    def get_event(
        self,
        events_service: EventService,
        event_id: UUID = Parameter(
            title="Event ID",
            description="The event to retrieve.",
        ),
    ) -> Event:
        """Get a event."""
        db_obj = events_service.get(event_id)
        return events_service.to_dto(db_obj)

    @post(
        operation_id="CreateEvent",
        name="events:create",
        summary="Create a new event.",
        cache_control=None,
        description="A event.",
        path=urls.EVENT_CREATE,
        sync_to_thread=False,
        dto=EventModifyDTO,
    )
    def create_event(
        self,
        events_service: EventService,
        current_user: User,
        data: DTOData[Event],
    ) -> Event:
        """Create a new event."""
        obj = data.as_builtins()
        obj.update({"owner_id": current_user.id})
        db_obj = events_service.create(obj)
        return events_service.to_dto(db_obj)

    @patch(
        operation_id="UpdateEvent",
        name="events:update",
        path=urls.EVENT_UPDATE,
        guards=[requires_event_ownership],
        sync_to_thread=False,
        dto=EventModifyDTO,
    )
    def update_event(
        self,
        data: DTOData[Event],
        events_service: EventService,
        event_id: UUID = Parameter(
            title="Event ID",
            description="The event to update.",
        ),
    ) -> Event:
        """Create a new event."""
        db_obj = events_service.update(event_id, data.as_builtins())
        return events_service.to_dto(db_obj)

    @delete(
        operation_id="DeleteEvent",
        name="events:delete",
        path=urls.EVENT_DELETE,
        summary="Remove Event",
        description="Removes a event and all associated data from the system.",
        guards=[requires_event_ownership],
        sync_to_thread=False,
        return_dto=None,
    )
    def delete_event(
        self,
        events_service: EventService,
        event_id: UUID = Parameter(
            title="Event ID",
            description="The event to delete.",
        ),
    ) -> None:
        """Delete a event from the system."""
        _ = events_service.delete(event_id)
