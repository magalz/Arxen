"""Alembic migrations against a disposable PostgreSQL/pgvector database."""

import os
import subprocess
import sys
from pathlib import Path

import psycopg

PROJECT_ROOT = Path(__file__).resolve().parents[2]
INITIAL_REVISION = "20260916_0001"


def run_alembic(database_url: str, *arguments: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["DATABASE_URL"] = database_url
    return subprocess.run(
        [sys.executable, "-m", "alembic", *arguments],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_upgrade_initial_prepares_empty_database(empty_database_url: str) -> None:
    result = run_alembic(empty_database_url, "upgrade", INITIAL_REVISION)

    assert result.returncode == 0, result.stderr
    with psycopg.connect(empty_database_url, connect_timeout=5) as connection:
        extension = connection.execute(
            "SELECT extversion FROM pg_extension WHERE extname = 'vector'"
        ).fetchone()
        revision = connection.execute(
            "SELECT version_num FROM alembic_version"
        ).fetchone()

    assert extension is not None
    assert revision == (INITIAL_REVISION,)
