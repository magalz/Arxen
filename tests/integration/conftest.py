"""Real database connections; missing infrastructure must never look like a pass."""

import os
from collections.abc import Iterator

import psycopg
import pytest


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
