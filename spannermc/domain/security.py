from __future__ import annotations

from typing import TYPE_CHECKING, Any

from litestar.contrib.jwt import OAuth2PasswordBearerAuth, Token
from sqlalchemy import select
from sqlalchemy.orm import noload

from spannermc.domain import urls
from spannermc.domain.accounts.models import User
from spannermc.domain.accounts.services import UserService
from spannermc.lib import constants, db, settings

if TYPE_CHECKING:
    from litestar.connection import ASGIConnection, Request

__all__ = ["current_user_from_token", "auth"]


def provide_user(request: Request[User, Token, Any]) -> User:
    """Get the user from the connection.

    Args:
        request: current connection.

    Returns:
    User
    """
    return request.user


def current_user_from_token(token: Token, connection: ASGIConnection[Any, Any, Any, Any]) -> User | None:
    """Lookup current user from local JWT token.

    Fetches the user information from the database


    Args:
        token (str): JWT Token Object
        connection (ASGIConnection[Any, Any, Any, Any]): ASGI connection.


    Returns:
        User: User record mapped to the JWT identifier
    """
    with UserService.new(
        session=db.config.provide_session(connection.app.state, connection.scope),
        statement=select(User).options(noload("*")),
    ) as service:
        user = service.get_one_or_none(email=token.sub)
        if user and user.is_active:
            return user
    return None


auth = OAuth2PasswordBearerAuth[User](
    retrieve_user_handler=current_user_from_token,
    token_secret=settings.app.SECRET_KEY,
    token_url=urls.ACCOUNT_LOGIN,
    exclude=[
        urls.OPENAPI_SCHEMA,
        constants.SYSTEM_HEALTH_URL,
        urls.ACCOUNT_LOGIN,
        urls.ACCOUNT_REGISTER,
        urls.KV_LIST,
        urls.KV_CREATE,
        urls.KV_DELETE,
        urls.KV_DETAIL,
        urls.KV_UPDATE,
    ],
)
