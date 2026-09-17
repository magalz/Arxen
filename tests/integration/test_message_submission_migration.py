"""Submission keys extend the schema without adopting historical messages."""

import os
import shutil
import subprocess
from pathlib import Path
from uuid import UUID, uuid4

import psycopg
import pytest

from arxen_api.persistence import CoreRepository

REVISION = "20260916_0004"


def migrate(url, revision, direction="upgrade"):
    pnpm = shutil.which("pnpm")
    assert pnpm is not None
    result = subprocess.run(
        [pnpm, "python:run", "alembic", direction, revision],
        cwd=Path(__file__).resolve().parents[2],
        env=os.environ.copy() | {"DATABASE_URL": url},
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def assert_schema(connection):
    assert connection.execute(
        "SELECT to_regclass('public.synthetic_message_submissions')"
    ).fetchone() == ("synthetic_message_submissions",)
    assert connection.execute("SELECT version_num FROM alembic_version").fetchone() == (
        REVISION,
    )


def test_empty_database_gets_repeatable_submission_schema(empty_database_url):
    with psycopg.connect(empty_database_url) as connection:
        assert (
            connection.execute(
                "SELECT tablename FROM pg_tables WHERE schemaname='public'"
            ).fetchall()
            == []
        )
    migrate(empty_database_url, REVISION)
    with psycopg.connect(empty_database_url) as connection:
        assert_schema(connection)
        assert connection.execute(
            "SELECT count(*) FROM synthetic_message_submissions"
        ).fetchone() == (0,)
    migrate(empty_database_url, REVISION)
    with psycopg.connect(empty_database_url) as connection:
        assert_schema(connection)


def test_upgrade_and_disposable_downgrade_preserve_all_historical_contracts(
    empty_database_url,
):
    migrate(empty_database_url, "20260916_0003")
    owner = uuid4()
    with psycopg.connect(empty_database_url) as connection:
        repo = CoreRepository(connection)
        case = repo.create_owned_case(owner)
        message = repo.add_message(case.id, "user", "Synthetic original")
        source = repo.create_message_source(case.id, message.id, 0, 9, "Synthetic")
        task = repo.create_task(case.id, "Synthetic task")
        event = repo.append_event(case.id, "case_created", "synthetic-service")
    for revision, direction in [
        (REVISION, "upgrade"),
        ("20260916_0003", "downgrade"),
        (REVISION, "upgrade"),
    ]:
        migrate(empty_database_url, revision, direction)
        with psycopg.connect(empty_database_url) as connection:
            if revision == REVISION:
                assert_schema(connection)
                assert connection.execute(
                    "SELECT count(*) FROM synthetic_message_submissions"
                ).fetchone() == (0,)
            else:
                assert connection.execute(
                    "SELECT to_regclass('public.synthetic_message_submissions')"
                ).fetchone() == (None,)
            repo = CoreRepository(connection)
            assert repo.get_owned_case(owner, case.id) == case
            assert repo.list_messages(case.id) == [message]
            assert repo.get_source(case.id, source.id) == source
            assert repo.get_task(case.id, task.id) == task
            assert repo.list_events(case.id) == [event]
            assert connection.execute(
                "SELECT extname FROM pg_extension WHERE extname='vector'"
            ).fetchone() == ("vector",)


@pytest.mark.parametrize(
    "violation",
    [
        "wrong_owner",
        "wrong_case",
        "nil_key",
        "null_key",
        "duplicate_key",
        "duplicate_message",
    ],
)
def test_real_constraints_protect_submission_scope(core_connection, violation):
    assert core_connection.execute(
        "SELECT to_regclass('public.synthetic_message_submissions')"
    ).fetchone() == ("synthetic_message_submissions",)
    owner, other_owner, key = uuid4(), uuid4(), uuid4()
    repo = CoreRepository(core_connection)
    case = repo.create_owned_case(owner)
    other = repo.create_owned_case(other_owner)
    message = repo.add_message(case.id, "user", "Synthetic")
    second = repo.add_message(case.id, "user", "Second")
    statement = (
        "INSERT INTO synthetic_message_submissions "
        "(case_id, owner_user_id, client_message_id, message_id) VALUES (%s,%s,%s,%s)"
    )
    core_connection.execute(statement, (case.id, owner, key, message.id))
    values = {
        "wrong_owner": (case.id, uuid4(), uuid4(), second.id),
        "wrong_case": (other.id, other_owner, uuid4(), second.id),
        "nil_key": (case.id, owner, UUID(int=0), second.id),
        "null_key": (case.id, owner, None, second.id),
        "duplicate_key": (case.id, owner, key, second.id),
        "duplicate_message": (case.id, owner, uuid4(), message.id),
    }
    with pytest.raises(psycopg.IntegrityError), core_connection.transaction():
        core_connection.execute(statement, values[violation])


@pytest.mark.parametrize(
    "operation",
    [
        "UPDATE synthetic_message_submissions SET client_message_id=%s "
        "WHERE message_id=%s",
        "DELETE FROM synthetic_message_submissions "
        "WHERE client_message_id=%s AND message_id=%s",
    ],
)
def test_committed_submission_cannot_be_reassigned_or_removed(
    core_connection, operation
):
    assert core_connection.execute(
        "SELECT to_regclass('public.synthetic_message_submissions')"
    ).fetchone() == ("synthetic_message_submissions",)
    owner, key = uuid4(), uuid4()
    repo = CoreRepository(core_connection)
    case = repo.create_owned_case(owner)
    message = repo.add_message(case.id, "user", "Synthetic")
    core_connection.execute(
        "INSERT INTO synthetic_message_submissions VALUES (%s,%s,%s,%s)",
        (case.id, owner, key, message.id),
    )
    with pytest.raises(psycopg.errors.CheckViolation), core_connection.transaction():
        core_connection.execute(operation, (key, message.id))
