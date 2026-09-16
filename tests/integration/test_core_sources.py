"""A source identifies an exact, preserved message passage within its case."""

from uuid import uuid4

import psycopg
import pytest

from arxen_api.persistence import CoreRepository


def test_source_resolves_exact_unicode_passage_in_its_case(core_connection) -> None:
    repository = CoreRepository(core_connection)
    case = repository.create_case()
    message = repository.add_message(case.id, "user", "Relato: ação 🧪 confirmada.")
    excerpt = "ação 🧪"
    start = message.content.index(excerpt)
    end = start + len(excerpt)

    source = repository.create_message_source(case.id, message.id, start, end, excerpt)

    assert source.id.version == 4
    assert source.kind == "message"
    assert source.message_id == message.id
    assert source.excerpt == message.content[source.start_offset : source.end_offset]
    assert repository.get_source(case.id, source.id) == source
    assert repository.get_source(uuid4(), source.id) is None
    assert repository.get_source(case.id, uuid4()) is None


@pytest.mark.parametrize("other_case", [False, True])
def test_database_rejects_missing_or_cross_case_origin(
    core_connection, other_case
) -> None:
    repository = CoreRepository(core_connection)
    case = repository.create_case()
    second_case = repository.create_case()
    message = repository.add_message(case.id, "user", "Synthetic text")
    repository.create_message_source(case.id, message.id, 0, 9, "Synthetic")
    case_id = second_case.id if other_case else case.id
    message_id = message.id if other_case else uuid4()

    with (
        pytest.raises(psycopg.errors.ForeignKeyViolation),
        core_connection.transaction(),
    ):
        core_connection.execute(
            "INSERT INTO sources "
            "(case_id, message_id, start_offset, end_offset, excerpt) "
            "VALUES (%s, %s, 0, 9, 'Synthetic')",
            (case_id, message_id),
        )


@pytest.mark.parametrize(
    ("start", "end", "excerpt", "kind"),
    [
        (-1, 3, "abc", "message"),
        (0, 0, "", "message"),
        (3, 2, "", "message"),
        (0, 7, "abcdef", "message"),
        (0, 3, "wrong", "message"),
        (None, 3, "abc", "message"),
        (0, None, "abc", "message"),
        (0, 3, None, "message"),
        (0, 3, "abc", "pdf"),
        (0, 3, "abc", None),
    ],
)
def test_database_rejects_invalid_or_invented_locator(
    core_connection, start, end, excerpt, kind
) -> None:
    repository = CoreRepository(core_connection)
    case = repository.create_case()
    message = repository.add_message(case.id, "user", "abcdef")
    original = repository.create_message_source(case.id, message.id, 0, 3, "abc")

    with pytest.raises(psycopg.IntegrityError), core_connection.transaction():
        core_connection.execute(
            "INSERT INTO sources "
            "(case_id, message_id, start_offset, end_offset, excerpt, kind) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (case.id, message.id, start, end, excerpt, kind),
        )

    assert repository.get_source(case.id, original.id) == original


@pytest.mark.parametrize(
    "statement",
    [
        "UPDATE sources SET excerpt = 'replacement' WHERE id = %s",
        "DELETE FROM sources WHERE id = %s",
    ],
)
def test_source_reference_cannot_be_retargeted_or_deleted(
    core_connection, statement
) -> None:
    repository = CoreRepository(core_connection)
    case = repository.create_case()
    message = repository.add_message(case.id, "user", "Synthetic preserved source")
    source = repository.create_message_source(case.id, message.id, 0, 9, "Synthetic")

    with pytest.raises(psycopg.errors.CheckViolation), core_connection.transaction():
        core_connection.execute(statement, (source.id,))

    assert repository.get_source(case.id, source.id) == source
