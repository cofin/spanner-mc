from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, cast

from google.cloud import spanner  # type: ignore[attr-defined]
from litestar.contrib.sqlalchemy.plugins.init.config import (
    SQLAlchemySyncConfig,
)
from litestar.contrib.sqlalchemy.plugins.init.config.common import SESSION_SCOPE_KEY, SESSION_TERMINUS_ASGI_EVENTS
from litestar.contrib.sqlalchemy.plugins.init.plugin import SQLAlchemyInitPlugin
from litestar.status_codes import HTTP_200_OK, HTTP_300_MULTIPLE_CHOICES
from litestar.utils import (
    delete_litestar_scope_state,
    get_litestar_scope_state,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from spannermc.lib import constants, settings

__all__ = ["before_send_handler", "session"]


if TYPE_CHECKING:
    from collections.abc import Iterator

    from litestar.types import Message, Scope
    from sqlalchemy.orm import Session


def before_send_handler(message: Message, scope: Scope) -> None:
    """Handle database connection before sending response.

    Custom `before_send_handler` for SQLAlchemy plugin that inspects the status of response and commits, or rolls back the database.

    Args:
        message: ASGI message
        _:
        scope: ASGI scope
    """
    session = cast("Session | None", get_litestar_scope_state(scope, SESSION_SCOPE_KEY))
    try:
        if session is not None and message["type"] == "http.response.start":
            if HTTP_200_OK <= message["status"] < HTTP_300_MULTIPLE_CHOICES:
                session.commit()
            else:
                session.rollback()
    finally:
        if session and message["type"] in SESSION_TERMINUS_ASGI_EVENTS:
            session.close()
            delete_litestar_scope_state(scope, SESSION_SCOPE_KEY)


spanner_client_options: dict[str, Any] = {"project": settings.cloud.GOOGLE_PROJECT}
if settings.db.API_ENDPOINT is not None:
    spanner_client_options.update({"client_options": {"api_endpoint": settings.db.API_ENDPOINT}})

spanner_client = spanner.Client(**spanner_client_options)
engine = create_engine(
    settings.db.URL,
    future=True,
    echo=settings.db.ECHO,
    echo_pool=True if settings.db.ECHO_POOL == "debug" else settings.db.ECHO_POOL,
    max_overflow=settings.db.POOL_MAX_OVERFLOW,
    pool_size=settings.db.POOL_SIZE,
    pool_timeout=settings.db.POOL_TIMEOUT,
    pool_recycle=settings.db.POOL_RECYCLE,
    pool_pre_ping=settings.db.POOL_PRE_PING,
    pool_use_lifo=True,  # use lifo to reduce the number of idle connections
    poolclass=NullPool if settings.db.POOL_DISABLE else None,
    connect_args={"client": spanner_client},
)
session_factory: sessionmaker[Session] = sessionmaker(engine, expire_on_commit=False)
"""Database session factory.

See [`sessionmaker()`][sqlalchemy.orm.sessionmaker].
"""

config = SQLAlchemySyncConfig(
    session_dependency_key=constants.DB_SESSION_DEPENDENCY_KEY,
    engine_instance=engine,
    session_maker=session_factory,
    before_send_handler=before_send_handler,
)


plugin = SQLAlchemyInitPlugin(config=config)


@contextmanager
def session() -> Iterator[Session]:
    """Use this to get a database session where you can't in litestar.

    Returns:
        Iterator[Session]
    """
    with session_factory() as session:
        yield session
