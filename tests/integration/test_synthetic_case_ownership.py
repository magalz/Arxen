"""Ownership is persistent, singular and enforced by real relational constraints."""

from uuid import UUID, uuid4

import psycopg
import pytest

from arxen_api.persistence import CoreRepository


def assert_binding_exists(connection) -> None:
    assert connection.execute(
        "SELECT to_regclass('public.synthetic_case_owners')"
    ).fetchone() == ("synthetic_case_owners",)


def test_owned_case_is_readable_only_in_the_matching_identity_scope(
    core_connection,
) -> None:
    owner = uuid4()
    other = uuid4()
    repository = CoreRepository(core_connection)
    case = repository.create_owned_case(owner)
    assert case.title == "Novo caso"
    assert case.id.version == 4
    assert repository.get_owned_case(owner, case.id) == case
    assert repository.get_owned_case(other, case.id) is None
    assert repository.get_owned_case(owner, uuid4()) is None
    assert core_connection.execute(
        "SELECT owner_user_id FROM synthetic_case_owners WHERE case_id = %s", (case.id,)
    ).fetchone() == (owner,)

    internal = repository.create_case("Synthetic unassigned internal case")
    assert repository.get_owned_case(owner, internal.id) is None
    assert repository.get_owned_case(other, internal.id) is None


def test_ownership_uses_the_callers_commit_and_a_fresh_connection(
    core_database_url,
) -> None:
    owner = uuid4()
    with psycopg.connect(core_database_url) as connection:
        case = CoreRepository(connection).create_owned_case(owner, "Synthetic durable")
        with psycopg.connect(core_database_url) as observer:
            assert CoreRepository(observer).get_owned_case(owner, case.id) is None
            assert CoreRepository(observer).get_case(case.id) is None

    with psycopg.connect(core_database_url) as observer:
        assert CoreRepository(observer).get_owned_case(owner, case.id) == case


def test_caller_rollback_removes_both_case_and_binding(core_database_url) -> None:
    owner = uuid4()
    with pytest.raises(RuntimeError, match="Synthetic rollback"):
        with psycopg.connect(core_database_url) as connection:
            case = CoreRepository(connection).create_owned_case(owner)
            raise RuntimeError("Synthetic rollback")

    with psycopg.connect(core_database_url) as observer:
        assert CoreRepository(observer).get_case(case.id) is None
        assert CoreRepository(observer).get_owned_case(owner, case.id) is None
        assert observer.execute(
            "SELECT count(*) FROM synthetic_case_owners WHERE case_id = %s", (case.id,)
        ).fetchone() == (0,)


@pytest.mark.parametrize(
    "owner,error",
    [
        (None, psycopg.errors.NotNullViolation),
        (UUID(int=0), psycopg.errors.CheckViolation),
    ],
)
def test_database_rejects_absent_or_nil_owner(core_connection, owner, error) -> None:
    assert_binding_exists(core_connection)
    case = CoreRepository(core_connection).create_case()
    with pytest.raises(error):
        with core_connection.transaction():
            core_connection.execute(
                "INSERT INTO synthetic_case_owners (case_id, owner_user_id) "
                "VALUES (%s, %s)",
                (case.id, owner),
            )
    assert core_connection.execute(
        "SELECT count(*) FROM synthetic_case_owners WHERE case_id = %s", (case.id,)
    ).fetchone() == (0,)


def test_database_rejects_binding_to_a_nonexistent_case(core_connection) -> None:
    assert_binding_exists(core_connection)
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        with core_connection.transaction():
            core_connection.execute(
                "INSERT INTO synthetic_case_owners (case_id, owner_user_id) "
                "VALUES (%s, %s)",
                (uuid4(), uuid4()),
            )


def test_database_rejects_a_second_owner_for_the_same_case(core_connection) -> None:
    assert_binding_exists(core_connection)
    case = CoreRepository(core_connection).create_case()
    first_owner = uuid4()
    core_connection.execute(
        "INSERT INTO synthetic_case_owners (case_id, owner_user_id) VALUES (%s, %s)",
        (case.id, first_owner),
    )
    with pytest.raises(psycopg.errors.UniqueViolation):
        with core_connection.transaction():
            core_connection.execute(
                "INSERT INTO synthetic_case_owners (case_id, owner_user_id) "
                "VALUES (%s, %s)",
                (case.id, uuid4()),
            )
    assert core_connection.execute(
        "SELECT owner_user_id FROM synthetic_case_owners WHERE case_id = %s", (case.id,)
    ).fetchall() == [(first_owner,)]
