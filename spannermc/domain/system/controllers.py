from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypeVar

from litestar import Controller, MediaType, get
from litestar.response import Response
from sqlalchemy import text

from spannermc.domain.system import schemas
from spannermc.lib import constants, log

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

__all__ = ["SystemController"]


logger = log.get_logger()

OnlineOffline = TypeVar("OnlineOffline", bound=Literal["online", "offline"])


class SystemController(Controller):
    tags = ["System"]

    @get(
        operation_id="SystemHealth",
        name="system:health",
        path=constants.SYSTEM_HEALTH_URL,
        media_type=MediaType.JSON,
        cache=False,
        tags=["System"],
        summary="Health Check",
        description="Execute a health check against backend components.  Returns system information including database status.",
        signature_namespace={"SystemHealth": schemas.SystemHealth},
        sync_to_thread=False,
    )
    def check_system_health(self, db_session: Session) -> Response[schemas.SystemHealth]:
        """Check database available and returns app config info."""
        try:
            db_session.execute(text("select 1"))
            db_ping = True
        except ConnectionRefusedError:
            db_ping = False

        db_status = "online" if db_ping else "offline"
        healthy = bool(db_ping)
        if healthy:
            logger.debug("System Health", database_status=db_status)
        else:
            logger.warning("System Health Check Failed", database_status=db_status)

        return Response(
            content=schemas.SystemHealth(database_status=db_status),  # type: ignore
            status_code=200 if db_ping else 500,
            media_type=MediaType.JSON,
        )
