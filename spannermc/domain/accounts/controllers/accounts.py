"""User Account Controllers."""
from __future__ import annotations

from typing import TYPE_CHECKING

from litestar import Controller, delete, get, patch, post
from litestar.di import Provide
from litestar.params import Dependency, Parameter

from spannermc.domain import urls
from spannermc.domain.accounts import schemas
from spannermc.domain.accounts.dependencies import provides_user_service
from spannermc.domain.accounts.guards import requires_superuser
from spannermc.domain.accounts.services import UserService
from spannermc.lib import log

__all__ = ["AccountController"]


if TYPE_CHECKING:
    from uuid import UUID

    from litestar.contrib.repository.filters import FilterTypes
    from litestar.pagination import OffsetPagination


logger = log.get_logger()


class AccountController(Controller):
    """Account Controller."""

    tags = ["User Accounts"]
    guards = [requires_superuser]
    dependencies = {"users_service": Provide(provides_user_service)}
    signature_namespace = {"UserService": UserService}

    @get(
        operation_id="ListUsers",
        name="users:list",
        summary="List Users",
        description="Retrieve the users.",
        path=urls.ACCOUNT_LIST,
        sync_to_thread=False,
    )
    def list_users(
        self, users_service: UserService, filters: list[FilterTypes] = Dependency(skip_validation=True)
    ) -> OffsetPagination[schemas.User]:
        """List users."""
        results, total = users_service.list_and_count(*filters)
        return users_service.to_schema(schemas.User, results, total, *filters)

    @get(
        operation_id="GetUser",
        name="users:get",
        path=urls.ACCOUNT_DETAIL,
        summary="Retrieve the details of a user.",
        sync_to_thread=False,
    )
    def get_user(
        self,
        users_service: UserService,
        user_id: UUID = Parameter(
            title="User ID",
            description="The user to retrieve.",
        ),
    ) -> schemas.User:
        """Get a user."""
        db_obj = users_service.get(user_id)
        return users_service.to_schema(schemas.User, db_obj)

    @post(
        operation_id="CreateUser",
        name="users:create",
        summary="Create a new user.",
        cache_control=None,
        description="A user who can login and use the system.",
        path=urls.ACCOUNT_CREATE,
        sync_to_thread=False,
    )
    def create_user(
        self,
        users_service: UserService,
        data: schemas.UserCreate,
    ) -> schemas.User:
        """Create a new user."""
        obj = data.dict(exclude_unset=True, by_alias=False, exclude_none=True)
        db_obj = users_service.create(obj)
        return users_service.to_schema(schemas.User, db_obj)

    @patch(operation_id="UpdateUser", name="users:update", path=urls.ACCOUNT_UPDATE, sync_to_thread=False)
    def update_user(
        self,
        data: schemas.UserUpdate,
        users_service: UserService,
        user_id: UUID = Parameter(
            title="User ID",
            description="The user to update.",
        ),
    ) -> schemas.User:
        """Create a new user."""
        db_obj = users_service.update(user_id, data.dict(exclude_unset=True, by_alias=False, exclude_none=True))
        return users_service.to_schema(schemas.User, db_obj)

    @delete(
        operation_id="DeleteUser",
        name="users:delete",
        path=urls.ACCOUNT_DELETE,
        summary="Remove User",
        description="Removes a user and all associated data from the system.",
        sync_to_thread=False,
    )
    def delete_user(
        self,
        users_service: UserService,
        user_id: UUID = Parameter(
            title="User ID",
            description="The user to delete.",
        ),
    ) -> None:
        """Delete a user from the system."""
        _ = users_service.delete(user_id)
