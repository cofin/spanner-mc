from litestar.config.cors import CORSConfig

from spannermc.lib import settings

config = CORSConfig(allow_origins=settings.app.BACKEND_CORS_ORIGINS)
"""Default CORS config"""
