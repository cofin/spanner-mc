from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

from google.cloud import spanner  # type: ignore[attr-defined]
from litestar.contrib.sqlalchemy.plugins.init.config import (
    SQLAlchemySyncConfig,
)
from litestar.contrib.sqlalchemy.plugins.init.config.sync import autocommit_before_send_handler
from litestar.contrib.sqlalchemy.plugins.init.plugin import SQLAlchemyInitPlugin
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from spannermc.lib import constants, settings

__all__ = ["session"]


if TYPE_CHECKING:
    from collections.abc import Iterator

    from sqlalchemy.orm import Session


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
    before_send_handler=autocommit_before_send_handler,
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
