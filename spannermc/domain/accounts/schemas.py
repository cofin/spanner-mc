from __future__ import annotations

from uuid import UUID  # noqa: TCH003

from spannermc.lib.schema import CamelizedBaseSchema

__all__ = [
    "User",
    "UserCreate",
    "UserLogin",
    "UserSignup",
    "UserUpdate",
]


class User(CamelizedBaseSchema):
    """User properties to use for a response."""

    id: UUID
    email: str
    name: str | None
    is_superuser: bool
    is_active: bool
    is_verified: bool


class UserSignup(CamelizedBaseSchema):
    """User Registration Input."""

    email: str
    password: str
    name: str | None = None


class UserLogin(CamelizedBaseSchema):
    """Properties required to log in."""

    username: str
    password: str


# Properties to receive via API on creation
class UserCreate(CamelizedBaseSchema):
    """User Create Properties."""

    email: str
    password: str
    name: str | None = None
    is_superuser: bool | None = False
    is_active: bool | None = True
    is_verified: bool | None = False


# Properties to receive via API on update
class UserUpdate(CamelizedBaseSchema):
    """Properties to receive for user updates."""

    email: str | None = None
    name: str | None = None
    is_superuser: bool | None = False
    is_active: bool | None = False
    is_verified: bool | None = False


User.update_forward_refs()
