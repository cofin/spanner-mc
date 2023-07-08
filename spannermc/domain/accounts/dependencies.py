"""User Account Controllers."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import Session, noload

from spannermc.domain.accounts.models import User
from spannermc.domain.accounts.services import UserService
from spannermc.lib import log

if TYPE_CHECKING:
    from collections.abc import Generator

__all__ = ["provides_user_service"]


logger = log.get_logger()


def provides_user_service(db_session: Session) -> Generator[UserService, None, None]:
    """Construct repository and service objects for the request."""
    with UserService.new(
        session=db_session,
        statement=select(User).order_by(User.email).options(noload("*")),
    ) as service:
        yield service
