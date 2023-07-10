from uuid import UUID

from litestar.connection import ASGIConnection
from litestar.exceptions import PermissionDeniedException
from litestar.handlers.base import BaseRouteHandler

__all__ = ["requires_event_ownership"]


def requires_event_ownership(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    """Verify that the connection user is the event owner.

    Args:
        connection (ASGIConnection): _description_
        _ (BaseRouteHandler): _description_

    Raises:
        PermissionDeniedException: _description_
    """
    event_id = UUID(connection.path_params["event_id"])
    if connection.user.is_superuser:
        return
    if any(user_event.event.id == event_id for user_event in connection.user.events):
        return
    raise PermissionDeniedException("Insufficient permissions to access event.")
