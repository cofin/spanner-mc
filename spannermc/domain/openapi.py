from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.spec import Contact

from spannermc.domain.security import auth
from spannermc.lib import settings

config = OpenAPIConfig(
    title=settings.openapi.TITLE or settings.app.NAME,
    version=settings.openapi.VERSION,
    contact=Contact(name=settings.openapi.CONTACT_NAME, email=settings.openapi.CONTACT_EMAIL),
    components=[auth.openapi_components],
    security=[auth.security_requirement],
    use_handler_docstrings=True,
    root_schema_site="swagger",
)
"""OpenAPI config for spannermc.  See OpenAPISettings for configuration."""
