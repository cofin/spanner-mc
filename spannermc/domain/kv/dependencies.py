"""KeyValueStore deps."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from spannermc.domain.kv.models import KVStore
from spannermc.domain.kv.services import KVStoreService
from spannermc.lib import log

if TYPE_CHECKING:
    from collections.abc import Generator

    from sqlalchemy.orm import Session

__all__ = ["provides_kv_service"]


logger = log.get_logger()


def provides_kv_service(db_session: Session) -> Generator[KVStoreService, None, None]:
    """Construct repository and service objects for the request."""
    with KVStoreService.new(
        session=db_session,
        statement=select(KVStore).with_hint(KVStore.__table__, text="@{FORCE_INDEX=uk_kv_key}"),
    ) as service:
        yield service
