from __future__ import annotations

from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column

from spannermc.lib.db import orm

__all__ = ["KVStore"]


class KVStore(orm.DatabaseModel):
    """KV Store Model."""

    __tablename__ = "kv_store"  # type: ignore[assignment]
    __table_args__ = (Index("uk_kv_key", "key", unique=True), {"comment": "Database Key Value Store"})
    key: Mapped[str] = mapped_column(String(length=100), nullable=False)
    value: Mapped[str] = mapped_column(String(length=255))
