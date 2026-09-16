"""The synthetic binding extends the schema without adopting existing cases."""

import os
import shutil
import subprocess
from pathlib import Path

import psycopg

from arxen_api.persistence import CoreRepository

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SYNTHETIC_REVISION = "20260916_0003"


def migrate(database_url: str, *arguments: str) -> None:
    pnpm = shutil.which("pnpm")
    assert pnpm is not None, "pnpm is required for migration integration tests"
    result = subprocess.run(
        [pnpm, *arguments],
        cwd=PROJECT_ROOT,
        env=os.environ.copy() | {"DATABASE_URL": database_url},
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr


def assert_binding_schema(connection) -> None:
    assert connection.execute(
        "SELECT to_regclass('public.synthetic_case_owners')"
    ).fetchone() == ("synthetic_case_owners",)
    assert connection.execute("SELECT version_num FROM alembic_version").fetchone() == (
        SYNTHETIC_REVISION,
    )
    assert connection.execute(
        "SELECT extname FROM pg_extension WHERE extname = 'vector'"
    ).fetchone() == ("vector",)


def test_empty_database_reaches_synthetic_head_and_migration_is_repeatable(
    empty_database_url,
) -> None:
    with psycopg.connect(empty_database_url) as connection:
        assert (
            connection.execute(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
            ).fetchall()
            == []
        )

    migrate(empty_database_url, "python:run", "alembic", "upgrade", SYNTHETIC_REVISION)
    with psycopg.connect(empty_database_url) as connection:
        assert_binding_schema(connection)
        assert connection.execute("SELECT count(*) FROM cases").fetchone() == (0,)
        assert connection.execute(
            "SELECT count(*) FROM synthetic_case_owners"
        ).fetchone() == (0,)

    migrate(empty_database_url, "python:run", "alembic", "upgrade", SYNTHETIC_REVISION)
    with psycopg.connect(empty_database_url) as connection:
        assert_binding_schema(connection)
        assert connection.execute("SELECT count(*) FROM cases").fetchone() == (0,)


def test_upgrade_preserves_all_old_contracts_without_assigning_an_owner(
    empty_database_url,
) -> None:
    migrate(empty_database_url, "python:run", "alembic", "upgrade", "20260916_0002")
    with psycopg.connect(empty_database_url) as connection:
        repository = CoreRepository(connection)
        case = repository.create_case("Synthetic case predating identity")
        message = repository.add_message(case.id, "user", "Synthetic original")
        source = repository.create_message_source(
            case.id, message.id, 0, 9, "Synthetic"
        )
        task = repository.create_task(case.id, "Synthetic migration objective")
        event = repository.append_event(case.id, "case_created", "synthetic-service")

    migrate(empty_database_url, "python:run", "alembic", "upgrade", SYNTHETIC_REVISION)
    with psycopg.connect(empty_database_url) as connection:
        assert_binding_schema(connection)
        repository = CoreRepository(connection)
        assert repository.get_case(case.id) == case
        assert repository.list_messages(case.id) == [message]
        assert repository.get_source(case.id, source.id) == source
        assert repository.get_task(case.id, task.id) == task
        assert repository.list_events(case.id) == [event]
        assert connection.execute(
            "SELECT count(*) FROM synthetic_case_owners"
        ).fetchone() == (0,)

    # Only this fixture-owned disposable database is ever downgraded.
    migrate(empty_database_url, "python:run", "alembic", "downgrade", "20260916_0002")
    with psycopg.connect(empty_database_url) as connection:
        assert connection.execute(
            "SELECT to_regclass('public.synthetic_case_owners')"
        ).fetchone() == (None,)
        assert CoreRepository(connection).get_case(case.id) == case
        assert connection.execute(
            "SELECT extname FROM pg_extension WHERE extname = 'vector'"
        ).fetchone() == ("vector",)

    migrate(empty_database_url, "python:run", "alembic", "upgrade", SYNTHETIC_REVISION)
    with psycopg.connect(empty_database_url) as connection:
        assert_binding_schema(connection)
        repository = CoreRepository(connection)
        assert repository.get_case(case.id) == case
        assert repository.list_messages(case.id) == [message]
        assert repository.get_source(case.id, source.id) == source
        assert repository.get_task(case.id, task.id) == task
        assert repository.list_events(case.id) == [event]
        assert connection.execute(
            "SELECT count(*) FROM synthetic_case_owners"
        ).fetchone() == (0,)
