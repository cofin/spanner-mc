"""Definition of extra HTTP exceptions that aren't included in `Starlite`.

Also, defines functions that translate service and repository exceptions
into HTTP exceptions.
"""
from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from litestar.contrib.repository.exceptions import ConflictError, NotFoundError, RepositoryError
from litestar.exceptions import (
    HTTPException,
    InternalServerException,
    NotFoundException,
)
from litestar.middleware.exceptions.middleware import create_exception_response
from litestar.status_codes import HTTP_409_CONFLICT, HTTP_500_INTERNAL_SERVER_ERROR
from structlog.contextvars import bind_contextvars

__all__ = [
    "ApplicationError",
    "MissingDependencyError",
    "after_exception_hook_handler",
    "exception_to_http_response",
]


if TYPE_CHECKING:
    from typing import Any

    from litestar.connection import Request
    from litestar.middleware.exceptions.middleware import ExceptionResponseContent
    from litestar.response import Response
    from litestar.types import Scope


class ApplicationError(Exception):
    """Base exception type for the lib's custom exception types."""


class MissingDependencyError(ApplicationError, ValueError):
    """A required dependency is not installed."""

    def __init__(self, module: str, config: str | None = None) -> None:
        """Missing Dependency Error.

        Args:
        module: name of the package that should be installed
        config: name of the extra to install the package.
        """
        config = config if config else module
        super().__init__(
            f"You enabled {config} configuration but package {module!r} is not installed. "
            f'You may need to run: "poetry install litestar-saqlalchemy[{config}]"',
        )


class _HTTPConflictException(HTTPException):
    """Request conflict with the current state of the target resource."""

    status_code = HTTP_409_CONFLICT


async def after_exception_hook_handler(exc: Exception, _scope: Scope) -> None:
    """Binds `exc_info` key with exception instance as value to structlog
    context vars.

    This must be a coroutine so that it is not wrapped in a thread where we'll lose context.

    Args:
        exc: the exception that was raised.
        _scope: scope of the request
        _state: application state
    """
    if isinstance(exc, ApplicationError | RepositoryError):
        return
    if isinstance(exc, HTTPException) and exc.status_code < HTTP_500_INTERNAL_SERVER_ERROR:
        return
    bind_contextvars(exc_info=sys.exc_info())


def exception_to_http_response(
    request: Request[Any, Any, Any],
    exc: ApplicationError | RepositoryError,
) -> Response[ExceptionResponseContent]:
    """Transform repository exceptions to HTTP exceptions.

    Args:
        request: The request that experienced the exception.
        exc: Exception raised during handling of the request.

    Returns:
        Exception response appropriate to the type of original exception.
    """
    http_exc: type[HTTPException]
    if isinstance(exc, NotFoundError):
        http_exc = NotFoundException
    elif isinstance(exc, ConflictError | RepositoryError):
        http_exc = _HTTPConflictException
    else:
        http_exc = InternalServerException
    return create_exception_response(http_exc(detail=str(exc.__cause__)))
