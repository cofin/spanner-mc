from __future__ import annotations

from typing import Any

from litestar.exceptions import PermissionDeniedException
from pydantic import SecretStr

from spannermc.lib import crypt
from spannermc.lib.repository import SQLAlchemySyncRepository
from spannermc.lib.service.sqlalchemy import SQLAlchemySyncRepositoryService

from .models import User

__all__ = ["UserService", "UserRepository"]


class UserRepository(SQLAlchemySyncRepository[User]):
    """User SQLAlchemy Repository."""

    model_type = User


class UserService(SQLAlchemySyncRepositoryService[User]):
    """Handles database operations for users."""

    repository_type = UserRepository

    def __init__(self, **repo_kwargs: Any) -> None:
        self.repository: UserRepository = self.repository_type(**repo_kwargs)
        self.model_type = self.repository.model_type

    def authenticate(self, username: str, password: SecretStr | str) -> User:
        """Authenticate a user.

        Args:
            username (str): _description_
            password (SecretStr): _description_

        Raises:
            NotAuthorizedException: Raised when the user doesn't exist, isn't verified, or is not active.

        Returns:
            User: The user object
        """
        db_obj = self.get_one_or_none(email=username)
        if db_obj is None:
            raise PermissionDeniedException("User not found or password invalid")
        if db_obj.hashed_password is None:
            raise PermissionDeniedException("User not found or password invalid.")
        if not crypt.verify_password(password, db_obj.hashed_password):
            raise PermissionDeniedException("User not found or password invalid")
        if not db_obj.is_active:
            raise PermissionDeniedException("User account is inactive")
        return db_obj

    def update_password(self, data: dict[str, Any], db_obj: User) -> None:
        """Update stored user password.

        This is only used when not used IAP authentication.

        Args:
            data (UserPasswordUpdate): _description_
            db_obj (User): _description_

        Raises:
            PermissionDeniedException: _description_
        """
        if db_obj.hashed_password is None:
            raise PermissionDeniedException("User not found or password invalid.")
        if not crypt.verify_password(data["current_password"], db_obj.hashed_password):
            raise PermissionDeniedException("User not found or password invalid.")
        if not db_obj.is_active:
            raise PermissionDeniedException("User account is not active")
        db_obj.hashed_password = crypt.get_password_hash(data["new_password"])
        self.repository.update(db_obj)

    def to_model(self, data: User | dict[str, Any], operation: str | None = None) -> User:
        if isinstance(data, dict) and "password" in data:
            password: SecretStr | str | None = data.pop("password", None)
            if password is not None:
                password = SecretStr(password) if isinstance(password, str) else password
                data.update({"hashed_password": crypt.get_password_hash(password)})
        return super().to_model(data, operation)
