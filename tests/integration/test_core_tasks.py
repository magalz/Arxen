"""Task persistence has valid states without executing a worker or transitions."""

from uuid import uuid4

import psycopg
import pytest

from arxen_api.persistence import CoreRepository


def test_new_tasks_are_drafts_and_multiple_tasks_can_share_a_case(
    core_connection,
) -> None:
    repository = CoreRepository(core_connection)
    case = repository.create_case()

    first = repository.create_task(case.id, "Synthetic first objective")
    second = repository.create_task(case.id, "Synthetic second objective")

    assert first.state == second.state == "draft"
    assert first.id.version == 4
    assert first.id != second.id
    assert first.objective == "Synthetic first objective"
    assert repository.get_task(case.id, first.id) == first
    assert repository.get_task(uuid4(), first.id) is None
    assert repository.get_task(case.id, uuid4()) is None


@pytest.mark.parametrize(
    "state",
    [
        "draft",
        "queued",
        "running",
        "waiting_user",
        "waiting_budget",
        "pause_requested",
        "paused",
        "recovering",
        "completed",
        "failed",
        "cancelled",
    ],
)
def test_database_can_represent_each_normative_state(core_connection, state) -> None:
    repository = CoreRepository(core_connection)
    case = repository.create_case()
    repository.create_task(case.id, "Synthetic draft")
    row = core_connection.execute(
        "INSERT INTO tasks (case_id, objective, state) "
        "VALUES (%s, %s, %s) RETURNING id",
        (case.id, "Synthetic state fixture, not an executed transition", state),
    ).fetchone()

    task = repository.get_task(case.id, row[0])

    assert task is not None
    assert task.state == state


@pytest.mark.parametrize("state", [None, "done", "approved", "awaiting_user"])
def test_database_rejects_non_normative_state(core_connection, state) -> None:
    repository = CoreRepository(core_connection)
    case = repository.create_case()
    original = repository.create_task(case.id, "Synthetic original")

    with pytest.raises(psycopg.IntegrityError), core_connection.transaction():
        core_connection.execute(
            "INSERT INTO tasks (case_id, objective, state) VALUES (%s, %s, %s)",
            (case.id, "Synthetic invalid state", state),
        )

    assert repository.get_task(case.id, original.id) == original


@pytest.mark.parametrize("objective", [None, "", "   "])
def test_database_requires_an_objective(core_connection, objective) -> None:
    repository = CoreRepository(core_connection)
    case = repository.create_case()
    repository.create_task(case.id, "Synthetic existing objective")

    with pytest.raises(psycopg.IntegrityError), core_connection.transaction():
        core_connection.execute(
            "INSERT INTO tasks (case_id, objective) VALUES (%s, %s)",
            (case.id, objective),
        )


def test_task_requires_an_existing_case(core_connection) -> None:
    repository = CoreRepository(core_connection)
    with (
        pytest.raises(psycopg.errors.ForeignKeyViolation),
        core_connection.transaction(),
    ):
        repository.create_task(uuid4(), "Synthetic orphan")
