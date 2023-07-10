from __future__ import annotations

from typing import TYPE_CHECKING

from litestar.contrib.repository.handlers import on_app_init as _on_app_init
from litestar.contrib.sqlalchemy.repository import SQLAlchemySyncRepository

__all__ = ["on_app_init"]


if TYPE_CHECKING:
    from litestar.config.app import AppConfig


def on_app_init(app_config: "AppConfig") -> "AppConfig":
    """Executes on application init.  Injects signature namespaces."""
    app_config.signature_namespace.update(
        {
            "SQLAlchemySyncRepository": SQLAlchemySyncRepository,
        }
    )
    return _on_app_init(app_config)
