from __future__ import annotations

from uuid import UUID  # noqa: TCH003

from spannermc.lib.schema import CamelizedBaseSchema

__all__ = ["Event", "EventCreate", "EventUpdate"]


class Event(CamelizedBaseSchema):
    """Event properties to use for a response."""

    id: UUID
    name: str
    user_id: UUID


# Properties to receive via API on creation
class EventCreate(CamelizedBaseSchema):
    """Event Create Properties."""

    name: str


# Properties to receive via API on update
class EventUpdate(CamelizedBaseSchema):
    """Properties to receive for user updates."""

    name: str


Event.update_forward_refs()
