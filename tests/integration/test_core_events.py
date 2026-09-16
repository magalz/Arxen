"""Ordered, immutable task/case events, without an emitter or worker."""

from uuid import uuid4

import psycopg
import pytest
from psycopg.types.json import Jsonb

from arxen_api.persistence import CoreRepository


def test_event_order_and_cursor_are_scoped_to_a_case(core_connection) -> None:
    repository = CoreRepository(core_connection)
    case = repository.create_case()
    other_case = repository.create_case()
    task = repository.create_task(case.id, "Synthetic objective")

    first = repository.append_event(case.id, "case_created", "synthetic-service")
    second = repository.append_event(
        case.id,
        "task_created",
        "synthetic-service",
        task_id=task.id,
        payload={"state": "draft", "detail": {"synthetic": True}},
    )
    other = repository.append_event(other_case.id, "case_created", "synthetic-service")

    assert first.id.version == 4
    assert first.id != second.id
    assert first.sequence < second.sequence
    assert first.created_at == second.created_at
    assert first.task_id is None
    assert first.payload == {}
    assert second.task_id == task.id
    assert second.payload["detail"] == {"synthetic": True}
    assert repository.list_events(case.id) == [first, second]
    assert repository.list_events(case.id, after_sequence=first.sequence) == [second]
    assert repository.list_events(case.id, after_sequence=second.sequence) == []
    assert repository.list_events(other_case.id) == [other]
    assert repository.list_events(uuid4()) == []


@pytest.mark.parametrize("cross_case", [False, True])
def test_database_rejects_invalid_task_relation(core_connection, cross_case) -> None:
    repository = CoreRepository(core_connection)
    case = repository.create_case()
    other_case = repository.create_case()
    task = repository.create_task(case.id, "Synthetic task")
    repository.append_event(
        case.id, "task_created", "synthetic-service", task_id=task.id
    )

    with (
        pytest.raises(psycopg.errors.ForeignKeyViolation),
        core_connection.transaction(),
    ):
        core_connection.execute(
            "INSERT INTO events (case_id, task_id, event_type, actor) "
            "VALUES (%s, %s, 'task_created', 'synthetic-service')",
            (
                other_case.id if cross_case else case.id,
                task.id if cross_case else uuid4(),
            ),
        )


def test_case_event_requires_an_existing_case(core_connection) -> None:
    repository = CoreRepository(core_connection)
    with (
        pytest.raises(psycopg.errors.ForeignKeyViolation),
        core_connection.transaction(),
    ):
        repository.append_event(uuid4(), "case_created", "synthetic-service")


@pytest.mark.parametrize(
    ("event_type", "actor", "payload"),
    [
        (None, "service", {}),
        ("", "service", {}),
        ("   ", "service", {}),
        ("case_created", None, {}),
        ("case_created", "", {}),
        ("case_created", "   ", {}),
        ("case_created", "service", None),
        ("case_created", "service", []),
        ("case_created", "service", "text"),
    ],
)
def test_database_requires_type_actor_and_object_payload(
    core_connection, event_type, actor, payload
) -> None:
    repository = CoreRepository(core_connection)
    case = repository.create_case()
    original = repository.append_event(case.id, "case_created", "synthetic-service")

    with pytest.raises(psycopg.IntegrityError), core_connection.transaction():
        core_connection.execute(
            "INSERT INTO events (case_id, event_type, actor, payload) "
            "VALUES (%s, %s, %s, %s)",
            (case.id, event_type, actor, None if payload is None else Jsonb(payload)),
        )

    assert repository.list_events(case.id) == [original]


@pytest.mark.parametrize(
    "statement",
    [
        "UPDATE events SET actor = 'replacement' WHERE id = %s",
        "DELETE FROM events WHERE id = %s",
    ],
)
def test_events_cannot_be_rewritten_or_deleted(core_connection, statement) -> None:
    repository = CoreRepository(core_connection)
    case = repository.create_case()
    original = repository.append_event(case.id, "case_created", "synthetic-service")

    with pytest.raises(psycopg.errors.CheckViolation), core_connection.transaction():
        core_connection.execute(statement, (original.id,))

    assert repository.list_events(case.id) == [original]


def test_event_sequence_is_assigned_by_the_server(core_connection) -> None:
    repository = CoreRepository(core_connection)
    case = repository.create_case()
    repository.append_event(case.id, "case_created", "synthetic-service")

    with pytest.raises(psycopg.errors.CheckViolation), core_connection.transaction():
        core_connection.execute(
            "INSERT INTO events (case_id, sequence, event_type, actor) "
            "VALUES (%s, 100, 'case_created', 'synthetic-service')",
            (case.id,),
        )


def test_event_cursor_cannot_skip_an_uncommitted_predecessor(core_database_url) -> None:
    with psycopg.connect(core_database_url) as setup:
        repository = CoreRepository(setup)
        case = repository.create_case()
        other_case = repository.create_case()

    with (
        psycopg.connect(core_database_url, autocommit=True) as first_connection,
        psycopg.connect(core_database_url, autocommit=True) as second_connection,
    ):
        first_repository = CoreRepository(first_connection)
        second_repository = CoreRepository(second_connection)
        second_connection.execute("SET lock_timeout = '100ms'")
        with first_connection.transaction():
            first = first_repository.append_event(
                case.id, "observed", "synthetic-service"
            )
            with (
                pytest.raises(psycopg.errors.LockNotAvailable),
                second_connection.transaction(),
            ):
                second_repository.append_event(case.id, "observed", "synthetic-service")
            independent = second_repository.append_event(
                other_case.id, "observed", "synthetic-service"
            )
            assert independent.case_id == other_case.id

        second = second_repository.append_event(
            case.id, "observed", "synthetic-service"
        )
        assert second.sequence > first.sequence
        assert second_repository.list_events(
            case.id, after_sequence=first.sequence
        ) == [second]
