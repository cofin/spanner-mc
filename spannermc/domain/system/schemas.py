from typing import Literal

from spannermc.lib import settings
from spannermc.lib.schema import CamelizedBaseSchema

__all__ = ["SystemHealth"]


class SystemHealth(CamelizedBaseSchema):
    """Health check response schema."""

    app: str = settings.app.NAME
    version: str = settings.app.BUILD_NUMBER
    database_status: Literal["online", "offline"]
