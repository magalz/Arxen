"""Configuration behavior for database connectivity."""

import pytest

from arxen_api.settings import (
    ConfigurationError,
    DatabaseSettings,
    load_database_settings,
)


def test_database_url_is_required() -> None:
    with pytest.raises(ConfigurationError, match="DATABASE_URL is required"):
        load_database_settings({})


def test_database_url_rejects_non_postgresql_scheme() -> None:
    with pytest.raises(ConfigurationError, match="PostgreSQL URL"):
        load_database_settings({"DATABASE_URL": "sqlite:///arxen.db"})


def test_database_url_requires_database_name() -> None:
    with pytest.raises(ConfigurationError, match="database name"):
        load_database_settings({"DATABASE_URL": "postgresql://user:pass@localhost/"})


def test_database_settings_preserve_input_and_select_psycopg_driver() -> None:
    settings = load_database_settings(
        {"DATABASE_URL": "postgresql://user:pass@127.0.0.1:5433/arxen_test"}
    )

    assert settings == DatabaseSettings(
        database_url="postgresql://user:pass@127.0.0.1:5433/arxen_test"
    )
    assert (
        settings.sqlalchemy_url
        == "postgresql+psycopg://user:pass@127.0.0.1:5433/arxen_test"
    )
