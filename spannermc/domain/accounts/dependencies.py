"""User Account Controllers."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import noload

from spannermc.domain.accounts.models import User
from spannermc.domain.accounts.services import UserService
from spannermc.lib import log

__all__ = ["provides_user_service"]


logger = log.get_logger()

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from sqlalchemy.ext.asyncio import AsyncSession


async def provides_user_service(db_session: AsyncSession) -> AsyncGenerator[UserService, None]:
    """Construct repository and service objects for the request."""
    async with UserService.new(
        session=db_session,
        statement=select(User).order_by(User.email).options(noload("*")),
    ) as service:
        yield service
