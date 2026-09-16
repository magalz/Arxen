"""Migrate an empty database and persist all five contracts across connections."""

import os
import shutil
import subprocess
from pathlib import Path

import psycopg
import pytest

from arxen_api.persistence import CoreRepository

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_REVISION = "20260916_0002"


def run_pnpm(database_url: str, *arguments: str) -> subprocess.CompletedProcess[str]:
    pnpm = shutil.which("pnpm")
    assert pnpm is not None, "pnpm is required for the migration integration test"
    env = os.environ.copy()
    env["DATABASE_URL"] = database_url
    return subprocess.run(
        [pnpm, *arguments],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )


def test_empty_database_migrates_and_reopens_all_contracts(empty_database_url) -> None:
    with psycopg.connect(empty_database_url) as connection:
        assert (
            connection.execute(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
            ).fetchall()
            == []
        )

    result = run_pnpm(empty_database_url, "db:migrate")
    assert result.returncode == 0, result.stderr

    with psycopg.connect(empty_database_url) as connection:
        repository = CoreRepository(connection)
        case = repository.create_case("Synthetic durable case")
        message = repository.add_message(case.id, "user", "Synthetic original")
        source = repository.create_message_source(
            case.id, message.id, 0, 9, "Synthetic"
        )
        task = repository.create_task(case.id, "Synthetic objective")
        event = repository.append_event(
            case.id, "task_created", "synthetic-service", task_id=task.id
        )
        with psycopg.connect(empty_database_url) as observer:
            assert CoreRepository(observer).get_case(case.id) is None

    result = run_pnpm(empty_database_url, "db:migrate")
    assert result.returncode == 0, result.stderr

    with psycopg.connect(empty_database_url) as reopened:
        repository = CoreRepository(reopened)
        assert repository.get_case(case.id) == case
        assert repository.list_messages(case.id) == [message]
        assert repository.get_source(case.id, source.id) == source
        assert repository.get_task(case.id, task.id) == task
        assert repository.list_events(case.id) == [event]
        assert reopened.execute(
            "SELECT version_num FROM alembic_version"
        ).fetchone() == (CORE_REVISION,)
        assert reopened.execute(
            "SELECT extname FROM pg_extension WHERE extname = 'vector'"
        ).fetchone() == ("vector",)


def test_caller_transaction_rolls_back_all_five_contracts(core_database_url) -> None:
    with pytest.raises(RuntimeError, match="Synthetic abort"):
        with psycopg.connect(core_database_url) as connection:
            repository = CoreRepository(connection)
            case = repository.create_case()
            message = repository.add_message(case.id, "user", "Synthetic original")
            source = repository.create_message_source(
                case.id, message.id, 0, 9, "Synthetic"
            )
            task = repository.create_task(case.id, "Synthetic task")
            repository.append_event(case.id, "task_created", "service", task_id=task.id)
            raise RuntimeError("Synthetic abort")

    with psycopg.connect(core_database_url) as reopened:
        repository = CoreRepository(reopened)
        assert repository.get_case(case.id) is None
        assert repository.list_messages(case.id) == []
        assert repository.get_source(case.id, source.id) is None
        assert repository.get_task(case.id, task.id) is None
        assert repository.list_events(case.id) == []


def test_downgrade_to_initial_and_upgrade_preserve_initial_extension(
    empty_database_url,
) -> None:
    result = run_pnpm(empty_database_url, "db:migrate")
    assert result.returncode == 0, result.stderr
    with psycopg.connect(empty_database_url) as connection:
        repository = CoreRepository(connection)
        case = repository.create_case()
        repository.append_event(case.id, "case_created", "synthetic-service")

    result = run_pnpm(
        empty_database_url, "python:run", "alembic", "downgrade", "20260916_0001"
    )
    assert result.returncode == 0, result.stderr
    with psycopg.connect(empty_database_url) as connection:
        assert connection.execute(
            "SELECT extname FROM pg_extension WHERE extname = 'vector'"
        ).fetchone() == ("vector",)
        assert connection.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
        ).fetchall() == [("alembic_version",)]

    result = run_pnpm(empty_database_url, "db:migrate")
    assert result.returncode == 0, result.stderr
    with psycopg.connect(empty_database_url) as connection:
        repository = CoreRepository(connection)
        case = repository.create_case()
        event = repository.append_event(case.id, "case_created", "synthetic-service")
        assert repository.list_events(case.id) == [event]
