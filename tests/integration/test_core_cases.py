"""Case persistence and database integrity, using synthetic data only."""

from datetime import UTC
from uuid import UUID, uuid4

import psycopg
import pytest

from arxen_api.persistence import CoreRepository


def test_case_roundtrip_uses_server_identity_and_utc(core_connection) -> None:
    core_connection.execute("SET LOCAL TIME ZONE 'America/Fortaleza'")
    repository = CoreRepository(core_connection)
    title = "Caso sintético: '); DROP TABLE cases; --"

    case = repository.create_case(title)
    another = repository.create_case()

    assert isinstance(case.id, UUID)
    assert case.id.version == 4
    assert case.id != another.id
    assert case.title == title
    assert another.title == "Novo caso"
    assert case.created_at.tzinfo is UTC
    assert repository.get_case(case.id) == case
    assert repository.get_case(uuid4()) is None


@pytest.mark.parametrize("title", [None, "", "   "])
def test_database_rejects_missing_or_blank_title(core_connection, title) -> None:
    repository = CoreRepository(core_connection)
    existing = repository.create_case("Synthetic existing case")

    with pytest.raises(psycopg.IntegrityError), core_connection.transaction():
        core_connection.execute("INSERT INTO cases (title) VALUES (%s)", (title,))

    assert repository.get_case(existing.id) == existing


def test_database_rejects_missing_operational_timestamp(core_connection) -> None:
    repository = CoreRepository(core_connection)
    repository.create_case()

    with pytest.raises(psycopg.errors.NotNullViolation), core_connection.transaction():
        core_connection.execute(
            "INSERT INTO cases (title, created_at) VALUES (%s, NULL)",
            ("Synthetic invalid instant",),
        )


def test_caller_rollback_does_not_leave_a_case(core_connection) -> None:
    repository = CoreRepository(core_connection)
    with core_connection.transaction(force_rollback=True):
        case = repository.create_case("Synthetic rolled-back case")

    assert repository.get_case(case.id) is None
