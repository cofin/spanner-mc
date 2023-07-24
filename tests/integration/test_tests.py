from typing import TYPE_CHECKING

from httpx import AsyncClient
from litestar import get
from sqlalchemy.orm import Session, sessionmaker

from spannermc.lib import db

if TYPE_CHECKING:
    from litestar import Litestar
    from sqlalchemy import Engine


def test_engine_on_app(app: "Litestar", engine: "Engine") -> None:
    """Test that the app's engine is patched.

    Args:
        app: The test Litestar instance
        engine: The test SQLAlchemy engine instance.
    """
    assert app.state[db.config.engine_app_state_key] is engine


def test_sessionmaker(app: "Litestar", sessionmaker: "sessionmaker[Session]") -> None:
    """Test that the sessionmaker is patched.

    Args:
        app: The test Litestar instance
        sessionmaker: The test SQLAlchemy sessionmaker factory.
    """
    assert db.session_factory is sessionmaker
    assert db.base.session_factory is sessionmaker


async def test_db_session_dependency(app: "Litestar", engine: "Engine") -> None:
    """Test that handlers receive session attached to patched engine.

    Args:
        app: The test Litestar instance
        engine: The patched SQLAlchemy engine instance.
    """

    @get("/db-session-test", opt={"exclude_from_auth": True})
    def db_session_dependency_patched(db_session: Session) -> dict[str, str]:
        return {"result": f"{db_session.bind is engine = }"}

    app.register(db_session_dependency_patched)
    # can't use test client as it always starts its own event loop
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.get("/db-session-test")
        assert response.json()["result"] == "db_session.bind is engine = True"
