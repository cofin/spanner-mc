import os
import sys
from collections.abc import AsyncIterator, Generator, Iterator
from typing import Any

import pytest
from httpx import AsyncClient
from litestar import Litestar
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from spannermc.domain.accounts.models import User
from spannermc.domain.security import auth
from spannermc.lib import db
from tests.docker_service import DockerServiceRegistry, spanner_responsive


@pytest.fixture(scope="session")
def docker_services() -> Generator[DockerServiceRegistry, None, None]:
    if sys.platform not in ("linux", "darwin") or os.environ.get("SKIP_DOCKER_TESTS"):
        pytest.skip("Docker not available on this platform")

    registry = DockerServiceRegistry()
    try:
        yield registry
    finally:
        registry.down()


@pytest.fixture(scope="session")
def docker_ip(docker_services: DockerServiceRegistry) -> str:
    return docker_services.docker_ip


@pytest.fixture()
async def spanner_service(docker_services: DockerServiceRegistry) -> None:
    await docker_services.start("spanner", check=spanner_responsive)  # type: ignore


@pytest.fixture(name="engine")
def fx_engine(docker_ip: str, monkeypatch: pytest.MonkeyPatch, spanner_service: None) -> Engine:
    """Postgresql instance for end-to-end testing.

    Args:
        docker_ip: IP address for TCP connection to Docker containers.
        monkeypatch: monkeypatch class
        spanner_service: Use the spanner service fixture
    Returns:
        Async SQLAlchemy engine instance.
    """
    monkeypatch.setenv("SPANNER_EMULATOR_HOST", "localhost:9010")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "emulator-test-project")

    return create_engine(
        "spanner+spanner:///projects/emulator-test-project/instances/test-instance/databases/test-database"
    )


@pytest.fixture(name="sessionmaker")
def fx_session_maker_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture(name="session")
def fx_session(sessionmaker: sessionmaker[Session]) -> Session:
    return sessionmaker()


@pytest.fixture(autouse=True)
def _seed_db(
    engine: Engine,
    sessionmaker: sessionmaker[Session],
    raw_users: list[User | dict[str, Any]],
) -> Iterator[None]:
    """Populate test database with.

    Args:
        engine: The SQLAlchemy engine instance.
        sessionmaker: The SQLAlchemy sessionmaker factory.
        raw_users: Test users to add to the database

    """

    from spannermc.domain.accounts.services import UserService
    from spannermc.lib.db import orm  # pylint: disable=[import-outside-toplevel,unused-import]

    metadata = orm.DatabaseModel.registry.metadata
    with engine.begin() as conn:
        metadata.drop_all(conn)
        metadata.create_all(conn)
    with UserService.new(sessionmaker()) as users_service:
        users_service.create_many(raw_users)
        users_service.repository.session.commit()

    yield


@pytest.fixture(autouse=True)
def _patch_db(
    app: "Litestar",
    engine: Engine,
    sessionmaker: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(db, "session_factory", sessionmaker)
    monkeypatch.setattr(db.base, "session_factory", sessionmaker)
    monkeypatch.setitem(app.state, db.config.engine_app_state_key, engine)
    monkeypatch.setitem(
        app.state,
        db.config.session_maker_app_state_key,
        sessionmaker(bind=engine, expire_on_commit=False),
    )


@pytest.fixture(name="client")
async def fx_client(app: Litestar) -> AsyncIterator[AsyncClient]:
    """Async client that calls requests on the spannermc.

    ```text
    ValueError: The future belongs to a different loop than the one specified as the loop argument
    ```
    """
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client


@pytest.fixture(name="superuser_token_headers")
def fx_superuser_token_headers() -> dict[str, str]:
    """Valid superuser token.

    ```text
    ValueError: The future belongs to a different loop than the one specified as the loop argument
    ```
    """
    return {"Authorization": f"Bearer {auth.create_token(identifier='superuser@example.com')}"}


@pytest.fixture(name="user_token_headers")
def fx_user_token_headers() -> dict[str, str]:
    """Valid user token.

    ```text
    ValueError: The future belongs to a different loop than the one specified as the loop argument
    ```
    """
    return {"Authorization": f"Bearer {auth.create_token(identifier='user@example.com')}"}
