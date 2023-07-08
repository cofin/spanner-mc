"""Application ORM configuration."""

from __future__ import annotations

from typing import Any

from litestar.contrib.sqlalchemy.base import UUIDAuditBase as TimestampedDatabaseModel
from litestar.contrib.sqlalchemy.base import UUIDBase as DatabaseModel
from litestar.contrib.sqlalchemy.base import orm_registry
from litestar.contrib.sqlalchemy.repository import ModelT  # noqa: TCH002

__all__ = ["DatabaseModel", "TimestampedDatabaseModel", "orm_registry", "model_from_dict"]


def model_from_dict(model: ModelT, **kwargs: Any) -> ModelT:
    """Return ORM Object from Dictionary."""
    data = {}
    for column in model.__table__.columns:
        if column.name in kwargs:
            data.update({column.name: kwargs.get(column.name)})
    return model(**data)  # type: ignore
