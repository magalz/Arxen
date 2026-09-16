"""Real database connections; missing infrastructure must never look like a pass."""

import os
import subprocess
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql


@pytest.fixture(scope="session")
def database_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL", "").strip()
    if not url:
        pytest.fail(
            "TEST_DATABASE_URL is required for integration tests. "
            "Point it at a disposable PostgreSQL database with pgvector available "
            "and run pnpm test:integration again.",
            pytrace=False,
        )
    return url


@pytest.fixture
def connection(database_url: str) -> Iterator[psycopg.Connection[tuple[object, ...]]]:
    with psycopg.connect(
        database_url, autocommit=True, connect_timeout=5
    ) as test_connection:
        # Explicit rollback includes extension creation when it was necessary.
        with test_connection.transaction(force_rollback=True):
            test_connection.execute("SET LOCAL statement_timeout = '5s'")
            test_connection.execute("CREATE EXTENSION IF NOT EXISTS vector")
            yield test_connection


@contextmanager
def temporary_database(base_url: str) -> Iterator[str]:
    """Create and drop only our own database; never reset the configured base."""
    name = f"arxen_contract_test_{uuid4().hex}"
    parsed = urlsplit(base_url)
    isolated_url = urlunsplit(parsed._replace(path=f"/{name}"))
    with psycopg.connect(base_url, autocommit=True, connect_timeout=5) as admin:
        admin.execute(
            sql.SQL("CREATE DATABASE {} TEMPLATE template0").format(
                sql.Identifier(name)
            )
        )
        try:
            yield isolated_url
        finally:
            admin.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(name)))


@pytest.fixture
def empty_database_url(database_url: str) -> Iterator[str]:
    with temporary_database(database_url) as isolated_url:
        yield isolated_url


@pytest.fixture(scope="session")
def core_database_url(database_url: str) -> Iterator[str]:
    with temporary_database(database_url) as isolated_url:
        env = os.environ.copy()
        env["DATABASE_URL"] = isolated_url
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=Path(__file__).resolve().parents[2],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode:
            pytest.fail(f"Cannot prepare core integration database: {result.stderr}")
        yield isolated_url


@pytest.fixture
def core_connection(
    core_database_url: str,
) -> Iterator[psycopg.Connection[tuple[object, ...]]]:
    with psycopg.connect(
        core_database_url, autocommit=True, connect_timeout=5
    ) as test_connection:
        with test_connection.transaction(force_rollback=True):
            test_connection.execute("SET LOCAL statement_timeout = '5s'")
            yield test_connection
