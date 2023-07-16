# pylint: disable=[invalid-name,import-outside-toplevel]
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

if TYPE_CHECKING:
    from litestar import Litestar

__all__ = ["create_app"]


def create_app() -> Litestar:
    """Application Builder.

    Returns:
        Litestar: configured database engine
    """

    import uvloop
    from litestar import Litestar
    from litestar.contrib.repository.exceptions import RepositoryError
    from litestar.di import Provide
    from pydantic import SecretStr

    from spannermc import domain
    from spannermc.domain.security import provide_user
    from spannermc.lib import (
        compression,
        constants,
        cors,
        db,
        dependencies,
        exceptions,
        log,
        otel,
        repository,
        settings,
    )

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    log.get_logger()

    application_dependencies = {constants.USER_DEPENDENCY_KEY: Provide(provide_user, sync_to_thread=False)}
    application_dependencies.update(dependencies.create_collection_dependencies())

    return Litestar(
        compression_config=compression.config,
        cors_config=cors.config,
        dependencies=application_dependencies,
        exception_handlers={
            exceptions.ApplicationError: exceptions.exception_to_http_response,  # type: ignore[dict-item]
            RepositoryError: exceptions.exception_to_http_response,  # type: ignore[dict-item]
        },
        debug=settings.app.DEBUG,
        before_send=[log.controller.BeforeSendHandler()],
        middleware=[log.controller.middleware_factory, otel.config.middleware],
        logging_config=log.config,
        openapi_config=domain.openapi.config,
        type_encoders={SecretStr: str, BaseModel: _base_model_encoder},
        route_handlers=[*domain.routes],
        plugins=[db.plugin],
        on_startup=[lambda: log.configure(log.default_processors)],  # type: ignore[arg-type]
        on_app_init=[domain.security.auth.on_app_init, repository.on_app_init],
        signature_namespace={
            **domain.signature_namespace,
        },
    )


def _base_model_encoder(value: BaseModel) -> dict[str, Any]:
    return value.model_dump(by_alias=True)
