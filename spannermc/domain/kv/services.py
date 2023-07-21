from __future__ import annotations

from typing import Any

from litestar.contrib.sqlalchemy.repository import SQLAlchemySyncRepository

from spannermc.lib.service.sqlalchemy import SQLAlchemySyncRepositoryService

from .models import KVStore

__all__ = ["KVStoreService", "KeyValueStoreRepository"]


class KeyValueStoreRepository(SQLAlchemySyncRepository[KVStore]):
    """KeyValueStore SQLAlchemy Repository."""

    model_type = KVStore


class KVStoreService(SQLAlchemySyncRepositoryService[KVStore]):
    """Handles database operations for users."""

    repository_type = KeyValueStoreRepository

    def __init__(self, **repo_kwargs: Any) -> None:
        self.repository: KeyValueStoreRepository = self.repository_type(**repo_kwargs)
        self.model_type = self.repository.model_type
