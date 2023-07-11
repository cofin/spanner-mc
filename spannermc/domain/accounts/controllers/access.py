"""User Account Controllers."""
from __future__ import annotations

from typing import TYPE_CHECKING

from litestar import Controller, MediaType, Response, get, post
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.params import Body

from spannermc.domain import security, urls
from spannermc.domain.accounts import schemas
from spannermc.domain.accounts.dependencies import provides_user_service
from spannermc.domain.accounts.guards import requires_active_user
from spannermc.domain.accounts.models import User
from spannermc.domain.accounts.services import UserService
from spannermc.lib import log

__all__ = ["AccessController", "provides_user_service"]


logger = log.get_logger()

if TYPE_CHECKING:
    from litestar.contrib.jwt import OAuth2Login


class AccessController(Controller):
    """User login and registration."""

    tags = ["Access"]
    dependencies = {"users_service": Provide(provides_user_service)}
    signature_namespace = {"UserService": UserService, "User": User}

    @post(
        operation_id="AccountLogin",
        name="account:login",
        path=urls.ACCOUNT_LOGIN,
        media_type=MediaType.JSON,
        cache=False,
        summary="Login",
        sync_to_thread=False,
    )
    def login(
        self,
        users_service: UserService,
        data: schemas.UserLogin = Body(title="OAuth2 Login", media_type=RequestEncodingType.URL_ENCODED),
    ) -> Response[OAuth2Login]:
        """Authenticate a user."""
        user = users_service.authenticate(data.username, data.password)
        return security.auth.login(user.email)

    @post(
        operation_id="AccountRegister",
        name="account:register",
        path=urls.ACCOUNT_REGISTER,
        cache=False,
        summary="Create User",
        description="Register a new account.",
        sync_to_thread=False,
    )
    def signup(self, users_service: UserService, data: schemas.UserSignup) -> schemas.User:
        """User Signup."""
        _data = data.dict(exclude_unset=True, by_alias=False, exclude_none=True)
        user = users_service.create(_data)
        return users_service.to_schema(schemas.User, user)

    @get(
        operation_id="AccountProfile",
        name="account:profile",
        path=urls.ACCOUNT_PROFILE,
        guards=[requires_active_user],
        summary="User Profile",
        description="User profile information.",
        sync_to_thread=False,
    )
    def profile(self, current_user: User, users_service: UserService) -> schemas.User:
        """User Profile."""
        return users_service.to_schema(schemas.User, current_user)
