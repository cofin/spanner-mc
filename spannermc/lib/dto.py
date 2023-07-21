from __future__ import annotations

from typing import TYPE_CHECKING

from litestar.contrib.sqlalchemy.dto import SQLAlchemyDTO
from litestar.dto import DataclassDTO, DTOConfig, dto_field

if TYPE_CHECKING:
    from collections.abc import Set

    from litestar.dto import RenameStrategy

__all__ = ["config", "dto_field", "DTOConfig", "SQLAlchemyDTO", "DataclassDTO"]


def config(
    include: Set[str] | None = None,
    exclude: Set[str] | None = None,
    rename_fields: dict[str, str] | None = None,
    rename_strategy: RenameStrategy | None = None,
    max_nested_depth: int | None = None,
) -> DTOConfig:
    """DTO Config Generator

    Returns:
        DTOConfig: Configured DTO class
    """
    default_kwargs = {"rename_strategy": "camel", "max_nested_depth": 2}
    if include is not None:
        include = set() if include is None else include
        default_kwargs.update({"include": include})
    else:
        exclude = {"sa_orm_sentinel"} if exclude is None else set(exclude).union({"sa_orm_sentinel"})
        default_kwargs.update({"exclude": exclude})
    if rename_fields:
        default_kwargs.update({"rename_fields": rename_fields})
    if rename_strategy:
        default_kwargs.update({"rename_strategy": rename_strategy})
    if max_nested_depth:
        default_kwargs.update({"max_nested_depth": max_nested_depth})
    return DTOConfig(**default_kwargs)  # type: ignore[arg-type]
