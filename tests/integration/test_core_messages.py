"""A case history is ordered, scoped and preserved in PostgreSQL."""

from uuid import uuid4

import psycopg
import pytest

from arxen_api.persistence import CoreRepository


def test_history_is_ordered_even_when_timestamps_tie(core_connection) -> None:
    repository = CoreRepository(core_connection)
    case = repository.create_case()
    other_case = repository.create_case()
    first = repository.add_message(case.id, "user", "Relato sintético: ação 🧪")
    second = repository.add_message(case.id, "assistant", "Resposta sintética")
    other = repository.add_message(other_case.id, "user", "Outro caso")

    assert first.created_at == second.created_at
    assert first.sequence < second.sequence
    assert first.id != second.id
    assert first.id.version == 4
    assert repository.list_messages(case.id) == [first, second]
    assert repository.list_messages(other_case.id) == [other]
    assert repository.list_messages(uuid4()) == []


def test_message_requires_an_existing_case(core_connection) -> None:
    repository = CoreRepository(core_connection)
    with (
        pytest.raises(psycopg.errors.ForeignKeyViolation),
        core_connection.transaction(),
    ):
        repository.add_message(uuid4(), "user", "Synthetic orphan")


@pytest.mark.parametrize(
    ("role", "content"),
    [(None, "text"), ("tool", "text"), ("user", None), ("user", ""), ("user", "   ")],
)
def test_database_rejects_invalid_message(core_connection, role, content) -> None:
    repository = CoreRepository(core_connection)
    case = repository.create_case()
    original = repository.add_message(case.id, "user", "Preserved synthetic message")

    with pytest.raises(psycopg.IntegrityError), core_connection.transaction():
        core_connection.execute(
            "INSERT INTO messages (case_id, role, content) VALUES (%s, %s, %s)",
            (case.id, role, content),
        )

    assert repository.list_messages(case.id) == [original]


@pytest.mark.parametrize(
    "statement",
    [
        "UPDATE messages SET content = 'replacement' WHERE id = %s",
        "DELETE FROM messages WHERE id = %s",
    ],
)
def test_confirmed_message_cannot_be_overwritten_or_deleted(
    core_connection, statement
) -> None:
    repository = CoreRepository(core_connection)
    case = repository.create_case()
    original = repository.add_message(case.id, "user", "Preserve this original")

    with pytest.raises(psycopg.errors.CheckViolation), core_connection.transaction():
        core_connection.execute(statement, (original.id,))

    assert repository.list_messages(case.id) == [original]


def test_message_sequence_cannot_be_supplied_by_caller(core_connection) -> None:
    repository = CoreRepository(core_connection)
    case = repository.create_case()
    repository.add_message(case.id, "user", "Synthetic first")

    with pytest.raises(psycopg.errors.CheckViolation), core_connection.transaction():
        core_connection.execute(
            "INSERT INTO messages (case_id, sequence, role, content) "
            "VALUES (%s, 100, 'user', 'Out of order')",
            (case.id,),
        )
