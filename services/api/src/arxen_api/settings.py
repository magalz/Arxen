"""Typed application configuration."""

from collections.abc import Mapping
from dataclasses import dataclass
from urllib.parse import urlsplit


class ConfigurationError(ValueError):
    """Raised when required application configuration is invalid."""


@dataclass(frozen=True)
class DatabaseSettings:
    """Database connectivity required by the application and migrations."""

    database_url: str

    @property
    def sqlalchemy_url(self) -> str:
        """Return a SQLAlchemy URL using the psycopg v3 driver."""
        if self.database_url.startswith("postgresql+psycopg://"):
            return self.database_url
        return self.database_url.replace("postgresql://", "postgresql+psycopg://", 1)


def load_database_settings(environ: Mapping[str, str]) -> DatabaseSettings:
    """Load and validate database settings from an environment mapping."""
    database_url = environ.get("DATABASE_URL", "").strip()
    if not database_url:
        raise ConfigurationError("DATABASE_URL is required")

    parsed = urlsplit(database_url)
    if parsed.scheme not in {"postgresql", "postgresql+psycopg"}:
        raise ConfigurationError("DATABASE_URL must be a PostgreSQL URL")
    if parsed.hostname is None:
        raise ConfigurationError("DATABASE_URL must include a database host")
    if not parsed.path.strip("/"):
        raise ConfigurationError("DATABASE_URL must include a database name")

    return DatabaseSettings(database_url=database_url)
