"""Application Modules."""
from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from litestar.contrib.jwt import OAuth2Login
from litestar.contrib.repository.filters import FilterTypes
from litestar.dto.factory import DTOData
from litestar.pagination import OffsetPagination
from litestar.types import TypeEncodersMap

from spannermc.domain.accounts.models import User
from spannermc.lib.service.generic import Service

from . import accounts, openapi, security, system, urls

if TYPE_CHECKING:
    from collections.abc import Mapping
    from typing import Any

    from litestar.types import ControllerRouterHandler


routes: list[ControllerRouterHandler] = [
    accounts.controllers.AccessController,
    accounts.controllers.AccountController,
    system.controllers.SystemController,
]

__all__ = [
    "system",
    "accounts",
    "urls",
    "security",
    "routes",
    "openapi",
    "signature_namespace",
]


signature_namespace: Mapping[str, Any] = {
    "Service": Service,
    "FilterTypes": FilterTypes,
    "UUID": UUID,
    "User": User,
    "OAuth2Login": OAuth2Login,
    "OffsetPagination": OffsetPagination,
    "UserService": accounts.services.UserService,
    "DTOData": DTOData,
    "TypeEncodersMap": TypeEncodersMap,
}
