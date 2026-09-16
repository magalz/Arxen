"""Alembic migration environment for Arxen."""

import os

from alembic import context
from sqlalchemy import create_engine, pool

from arxen_api.settings import load_database_settings

target_metadata = None


def database_url() -> str:
    """Return the validated database URL in SQLAlchemy psycopg form."""
    return load_database_settings(os.environ).sqlalchemy_url


def run_migrations_offline() -> None:
    """Render migrations without opening a database connection."""
    context.configure(
        url=database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations using an isolated SQLAlchemy connection."""
    engine = create_engine(database_url(), poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
