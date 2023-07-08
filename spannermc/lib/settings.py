"""All configuration via environment.

Take note of the environment variable prefixes required for each
settings class, except `AppSettings`.
"""
from __future__ import annotations

import binascii
import importlib
import io
import logging
import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Final, Literal

import google.auth
from dotenv import load_dotenv
from litestar.data_extractors import RequestExtractorField, ResponseExtractorField  # noqa: TCH002
from pydantic import BaseSettings as _BaseSettings
from pydantic import SecretBytes, ValidationError, validator

from spannermc import utils
from spannermc.lib import serialization
from spannermc.lib.cloud import gcp as gcp_secret_manager

__all__ = ["BASE_DIR", "BaseSettings", "app", "openapi", "server", "cloud", "db"]

logger = logging.getLogger()

DEFAULT_MODULE_NAME = "spannermc"
BASE_DIR: Final = utils.module_to_os_path(DEFAULT_MODULE_NAME)
version = importlib.metadata.version(DEFAULT_MODULE_NAME)


class BaseSettings(_BaseSettings):
    """Base Settings."""

    class Config:
        """Base Settings Config."""

        json_loads = serialization.from_json
        json_dumps = serialization.to_json
        case_sensitive = False
        validate_assignment = True
        orm_mode = True
        use_enum_values = True
        arbitrary_types_allowed = True
        env_file = ".env"
        env_file_encoding = "utf-8"


class ServerSettings(BaseSettings):
    """Server configurations."""

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_prefix = "SERVER_"

    APP_LOC: str = "spannermc.app:create_app"
    """Path to app executable, or factory."""
    APP_LOC_IS_FACTORY: bool = True
    """Indicate if APP_LOC points to an executable or factory."""
    HOST: str = "0.0.0.0"  # noqa: S104
    """Server network host."""
    KEEPALIVE: int = 65
    """Seconds to hold connections open (65 is > AWS lb idle timeout)."""
    PORT: int = 8080
    """Server port."""
    RELOAD: bool | None = None
    """Turn on hot reloading."""
    RELOAD_DIR: str = f"{BASE_DIR}"
    """Directories to watch for reloading."""
    HTTP_WORKERS: int | None = None
    """Number of HTTP Worker processes to be spawned by Uvicorn."""
    EXPIRATION: int = 60


#
class AppSettings(BaseSettings):
    """Generic application settings."""

    class Config:
        case_sensitive = True
        env_file = ".env"

    NAME: str = "Database Migration Assessment"
    """Application name."""
    BUILD_NUMBER: str = version
    """Identifier for CI build."""
    DEBUG: bool = False
    """Run `Litestar` with `debug=True`."""
    ENVIRONMENT: str = "prod"
    """'dev', 'prod', etc."""
    SECRET_KEY: SecretBytes
    """secret key"""
    JWT_ENCRYPTION_ALGORITHM: str = "HS256"
    """JWT encryption algorithm"""
    CSRF_COOKIE_NAME: str = "csrftoken"
    """CSRF Cookie Name to use when configured."""
    CSRF_COOKIE_SECURE: bool = False
    """CSRF Secure Cookie enforcement."""
    BACKEND_CORS_ORIGINS: list[str] = ["*"]
    """Backend CORS Origin configuration."""

    @property
    def slug(self) -> str:
        """Return a slugified name.

        Returns:
            `self.NAME`, all lowercase and hyphens instead of spaces.
        """
        return utils.slugify(self.NAME)

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(
        cls,
        value: str | list[str],
    ) -> list[str] | str:
        """Parse a list of origins."""
        if isinstance(value, list):
            return value
        if isinstance(value, str) and not value.startswith("["):
            return [host.strip() for host in value.split(",")]
        if isinstance(value, str) and value.startswith("[") and value.endswith("]"):
            return list(value)
        raise ValueError(value)

    @validator("SECRET_KEY", pre=True, always=True)
    def generate_secret_key(
        cls,
        value: SecretBytes | None,
    ) -> SecretBytes:
        """Generate a secret key."""
        if value is None:
            return SecretBytes(binascii.hexlify(os.urandom(32)))
        return value


# noinspection PyUnresolvedReferences
class OpenAPISettings(BaseSettings):
    """Configures OpenAPI for the application.

    Prefix all environment variables with `OPENAPI_`, e.g., `OPENAPI_TITLE`.

    Attributes:
    ----------
    TITLE : str
        OpenAPI document title.
    VERSION : str
        OpenAPI document version.
    CONTACT_NAME : str
        OpenAPI document contact name.
    CONTACT_EMAIL : str
        OpenAPI document contact email.
    """

    class Config:
        """OpenAPI Settings Config Metadata."""

        env_prefix = "OPENAPI_"
        case_sensitive = True

    TITLE: str | None
    VERSION: str = f"v{version}"
    CONTACT_NAME: str = "Admin"
    CONTACT_EMAIL: str = "admin@localhost"


# noinspection PyUnresolvedReferences
class DatabaseSettings(BaseSettings):
    """Configures the database for the application.

    Prefix all environment variables with `DB_`, e.g., `DB_URL`.

    Attributes:
    ----------
    ECHO : bool
        Enables SQLAlchemy engine logs.
    URL : PostgresDsn
        URL for database connection.
    DUCKDB_URL: str
        URI for duckdb. All analytics are done in-process and not stored by default.  Modify this to a file path if you'd like to store locally
    """

    class Config:
        """Database Settings Config Metadata."""

        env_prefix = "DB_"
        case_sensitive = True

    ECHO: bool = False
    ECHO_POOL: bool | Literal["debug"] = False
    POOL_DISABLE: bool = False
    POOL_MAX_OVERFLOW: int = 50
    POOL_SIZE: int = 10
    POOL_TIMEOUT: int = 30
    POOL_RECYCLE: int = 300
    POOL_PRE_PING: bool = True
    URL: str = "spanner+spanner:///projects/emulator-test-project/instances/test-instance/databases/test-database"
    MIGRATION_CONFIG: str = f"{BASE_DIR}/lib/db/alembic.ini"
    MIGRATION_PATH: str = f"{BASE_DIR}/lib/db/migrations"
    MIGRATION_DDL_VERSION_TABLE: str = "ddl_version"


# noinspection PyUnresolvedReferences
class CloudSettings(BaseSettings):
    """Google Cloud Configuration."""

    class Config:
        """Cloud Settings Config Metadata."""

        case_sensitive = True
        fields = {
            "GOOGLE_CREDENTIALS": {
                "env": "GOOGLE_APPLICATION_CREDENTIALS",
            },
            "GOOGLE_PROJECT": {"env": "GOOGLE_PROJECT_ID"},
            "ENV_SECRETS": {"env": "ENV_SECRETS"},
        }

    ACTIVE_CLOUD: str = "local"
    GOOGLE_PROJECT: str | None = None
    GOOGLE_CREDENTIALS: str | None = None
    ENV_SECRETS: str = "runtime-secrets"


class LogSettings(BaseSettings):
    """Log Settings."""

    class Config:
        """Log Settings Config Metadata."""

        env_prefix = "LOG_"
        case_sensitive = True

    # https://stackoverflow.com/a/1845097/6560549
    EXCLUDE_PATHS: str = r"\A(?!x)x"
    """Regex to exclude paths from logging."""
    HTTP_EVENT: str = "HTTP"
    """Log event name for logs from Starlite handlers."""
    INCLUDE_COMPRESSED_BODY: bool = False
    """Include 'body' of compressed responses in log output."""
    LEVEL: int = 20
    """Stdlib log levels. Only emit logs at this level, or higher."""
    OBFUSCATE_COOKIES: set[str] = {"session", "csrftoken", "token"}
    """Request cookie keys to obfuscate."""
    OBFUSCATE_HEADERS: set[str] = {
        "Authorization",
        "X-API-KEY",
        "cookie",
    }
    """Request header keys to obfuscate."""
    JOB_FIELDS: list[str] = [
        "function",
        "kwargs",
        "key",
        "scheduled",
        "attempts",
        "completed",
        "queued",
        "started",
        "result",
        "error",
    ]
    """Attributes of the SAQ [`Job`](https://github.com/tobymao/saq/blob/master/saq/job.py)
    to be logged.
    """
    REQUEST_FIELDS: list[RequestExtractorField] = [
        "path",
        "method",
        "content_type",
        "headers",
        "cookies",
        "query",
        "path_params",
        # "body",
    ]
    """Attributes of the [Request][starlite.connection.request.Request] to be logged."""
    RESPONSE_FIELDS: list[ResponseExtractorField] = [
        "status_code",
        "cookies",
        "headers",
        # "body",
    ]
    """Attributes of the [Response][starlite.response.Response] to be logged."""
    SQLALCHEMY_LEVEL: int = 30
    """Level to log SAQ logs."""
    UVICORN_ACCESS_LEVEL: int = 30
    """Level to log uvicorn access logs."""
    UVICORN_ERROR_LEVEL: int = 30
    """Level to log uvicorn error logs."""


@lru_cache
def get_settings(
    env: str | None = None,
) -> tuple[AppSettings, DatabaseSettings, OpenAPISettings, ServerSettings, CloudSettings, LogSettings]:
    """Load Settings file.

    Returns:
        Settings: _description_
    """
    active_cloud = os.environ.get("CLOUD", "local")
    secret_id = os.environ.get("ENV_SECRETS", None)
    env_file_exists = Path(f"{os.curdir}/.env").is_file()

    local_service_account_exists = Path(f"{os.curdir}/service_account.json").is_file()
    if local_service_account_exists:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service_account.json"
    project_id = os.environ.get("GOOGLE_PROJECT_ID", None)
    if project_id is None:
        _, project_id = google.auth.default()
        os.environ["GOOGLE_PROJECT_ID"] = project_id
    if not env_file_exists and secret_id:
        secret = gcp_secret_manager.get_secret(project_id, secret_id)
        load_dotenv(stream=io.StringIO(secret))
    elif active_cloud == "aws":
        from spannermc.lib.cloud import aws as aws_secret_manager

        if not env_file_exists and secret_id:
            secret = aws_secret_manager.get_secret(secret_id)
            load_dotenv(stream=io.StringIO(secret))

    try:
        app: AppSettings = AppSettings.parse_obj({})
        db: DatabaseSettings = DatabaseSettings.parse_obj({})
        openapi: OpenAPISettings = OpenAPISettings.parse_obj({})
        server: ServerSettings = ServerSettings.parse_obj({})
        cloud: CloudSettings = CloudSettings.parse_obj({})
        log: LogSettings = LogSettings.parse_obj({})
    except ValidationError as e:
        logger.fatal("Could not load settings. %s", e)
        sys.exit(1)
    return (app, db, openapi, server, cloud, log)


app, db, openapi, server, cloud, log = get_settings()
