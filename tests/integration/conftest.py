import asyncio
import contextlib
import os
import timeit
from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from google.auth.credentials import AnonymousCredentials
from google.cloud import spanner
from httpx import AsyncClient
from litestar import Litestar
from sqlalchemy import Engine, create_engine
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import Session, sessionmaker

from spannermc.domain.accounts.models import User
from spannermc.domain.security import auth
from spannermc.lib import db

if TYPE_CHECKING:
    from collections import abc

    from pytest_docker.plugin import Services


here = Path(__file__).parent


@pytest.fixture(scope="session")
def docker_compose_file() -> Path:
    """Load docker compose file.

    Returns:
        Path to the docker-compose file for end-to-end test environment.
    """
    return here / "docker-compose.yml"


async def wait_until_responsive(
    check: "abc.Callable[..., abc.Awaitable]",
    timeout: float,
    pause: float,
    **kwargs: Any,
) -> None:
    """Wait until a service is responsive.

    Args:
        check: Coroutine, return truthy value when waiting should stop.
        timeout: Maximum seconds to wait.
        pause: Seconds to wait between calls to `check`.
        **kwargs: Given as kwargs to `check`.
    """
    ref = timeit.default_timer()
    now = ref
    while (now - ref) < timeout:
        if await check(**kwargs):
            return
        await asyncio.sleep(pause)
        now = timeit.default_timer()

    raise Exception("Timeout reached while waiting on service!")


async def db_responsive(host: str) -> bool:
    """Args:
        host: docker IP address.

    Returns:
        Boolean indicating if we can connect to the database.
    """
    try:
        os.environ["SPANNER_EMULATOR_HOST"] = "localhost:9010"
        os.environ["GOOGLE_CLOUD_PROJECT"] = "emulator-test-project"
        spanner_client = spanner.Client(project="emulator-test-project", credentials=AnonymousCredentials())
        instance = spanner_client.instance("test-instance")
        with contextlib.suppress(Exception):
            instance.create()

        database = instance.database("test-database")
        with contextlib.suppress(Exception):
            database.create()

        with database.snapshot() as snapshot:
            resp = list(snapshot.execute_sql("SELECT 1"))[0]
        return resp[0] == 1
    except Exception:  # noqa: BLE001
        return False


@pytest.fixture(scope="session", autouse=True)
async def _containers(docker_ip: str, docker_services: "Services") -> None:  # pylint: disable=unused-argument
    """Starts containers for required services, fixture waits until they are
    responsive before returning.

    Args:
        docker_ip: the test docker IP
        docker_services: the test docker services
    """
    await wait_until_responsive(timeout=30.0, pause=0.1, check=db_responsive, host=docker_ip)


@pytest.fixture(name="engine")
def fx_engine(docker_ip: str, monkeypatch: pytest.MonkeyPatch) -> Engine:
    """Postgresql instance for end-to-end testing.

    Args:
        docker_ip: IP address for TCP connection to Docker containers.
        monkeypatch: monkeypatch class
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
    engine: AsyncEngine,
    sessionmaker: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(db, "async_session_factory", sessionmaker)
    monkeypatch.setattr(db.base, "async_session_factory", sessionmaker)
    monkeypatch.setitem(app.state, db.config.engine_app_state_key, engine)
    monkeypatch.setitem(
        app.state,
        db.config.session_maker_app_state_key,
        async_sessionmaker(bind=engine, expire_on_commit=False),
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
