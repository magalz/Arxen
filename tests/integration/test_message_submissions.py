"""Real transactions preserve authorized, idempotent message submission."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import psycopg
import pytest

from arxen_api.conversation import MessageConflict
from arxen_api.persistence import CoreRepository


def test_submission_replay_conflict_and_authorized_history(core_connection):
    repo = CoreRepository(core_connection)
    owner, other, key = uuid4(), uuid4(), uuid4()
    case = repo.create_owned_case(owner)
    result = repo.submit_owned_message(owner, case.id, key, "  Synthetic 🧪\n ")
    assert result is not None
    message, created = result
    assert created is True
    assert message.role == "user"
    assert message.id.version == 4 and message.id != key
    assert message.content == "  Synthetic 🧪\n "
    assert message.created_at.utcoffset().total_seconds() == 0
    assert repo.submit_owned_message(owner, case.id, key, message.content) == (
        message,
        False,
    )
    with pytest.raises(MessageConflict):
        repo.submit_owned_message(owner, case.id, key, "Changed")
    assert repo.submit_owned_message(other, case.id, key, "Changed") is None
    assert repo.list_owned_messages(owner, case.id, after_sequence=0, limit=10) == [
        message
    ]
    assert repo.list_owned_messages(other, case.id, after_sequence=0, limit=10) is None
    assert repo.list_messages(case.id) == [message]
    assert core_connection.execute(
        "SELECT message_sequence FROM cases WHERE id=%s", (case.id,)
    ).fetchone() == (1,)


def test_keys_are_scoped_to_case_and_history_has_no_side_effects(core_connection):
    repo = CoreRepository(core_connection)
    owner, key = uuid4(), uuid4()
    case = repo.create_owned_case(owner)
    second_case = repo.create_owned_case(owner)
    internal = repo.create_case()
    assert repo.list_owned_messages(owner, case.id, after_sequence=0, limit=10) == []
    assert repo.submit_owned_message(owner, internal.id, key, "Denied") is None
    assert repo.submit_owned_message(owner, uuid4(), key, "Denied") is None
    assert (
        repo.list_owned_messages(owner, internal.id, after_sequence=0, limit=10) is None
    )
    first = repo.submit_owned_message(owner, case.id, key, "First")[0]
    legacy = repo.add_message(case.id, "assistant", "Synthetic internal answer")
    second = repo.submit_owned_message(owner, case.id, uuid4(), "Second")[0]
    separate = repo.submit_owned_message(owner, second_case.id, key, "Other case")[0]
    assert separate.id != first.id
    assert repo.list_owned_messages(owner, case.id, after_sequence=0, limit=2) == [
        first,
        legacy,
    ]
    assert repo.list_owned_messages(
        owner, case.id, after_sequence=legacy.sequence, limit=2
    ) == [second]
    assert (
        repo.list_owned_messages(
            owner, case.id, after_sequence=second.sequence, limit=2
        )
        == []
    )
    assert repo.list_messages(case.id) == [first, legacy, second]


def test_submission_commit_and_rollback_use_callers_connection(core_database_url):
    owner, key = uuid4(), uuid4()
    with psycopg.connect(core_database_url) as connection:
        case = CoreRepository(connection).create_owned_case(owner)
    with psycopg.connect(core_database_url) as connection:
        message, created = CoreRepository(connection).submit_owned_message(
            owner, case.id, key, "Durable"
        )
        assert created
        with psycopg.connect(core_database_url) as observer:
            assert CoreRepository(observer).list_messages(case.id) == []
    with psycopg.connect(core_database_url) as connection:
        assert CoreRepository(connection).submit_owned_message(
            owner, case.id, key, "Durable"
        ) == (message, False)
    with pytest.raises(RuntimeError, match="Synthetic abort"):
        with psycopg.connect(core_database_url) as connection:
            CoreRepository(connection).submit_owned_message(
                owner, case.id, uuid4(), "Aborted"
            )
            raise RuntimeError("Synthetic abort")
    with psycopg.connect(core_database_url) as observer:
        assert CoreRepository(observer).list_messages(case.id) == [message]
        assert observer.execute(
            "SELECT count(*) FROM synthetic_message_submissions WHERE case_id=%s",
            (case.id,),
        ).fetchone() == (1,)


def test_autocommit_without_a_transaction_is_rejected(core_database_url):
    with psycopg.connect(core_database_url, autocommit=True) as connection:
        with pytest.raises(ValueError, match="transaction"):
            CoreRepository(connection).submit_owned_message(
                uuid4(), uuid4(), uuid4(), "Unsafe"
            )


@pytest.mark.parametrize("different_content", [False, True])
def test_concurrent_submissions_serialize_replay_or_conflict(
    core_database_url, different_content
):
    owner, key = uuid4(), uuid4()
    with psycopg.connect(core_database_url) as connection:
        case = CoreRepository(connection).create_owned_case(owner)
    barrier = Barrier(2)

    def submit(content):
        try:
            with psycopg.connect(core_database_url) as connection:
                connection.execute("SET LOCAL statement_timeout='10s'")
                barrier.wait(timeout=10)
                return CoreRepository(connection).submit_owned_message(
                    owner, case.id, key, content
                )
        except MessageConflict:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as executor:
        a = executor.submit(submit, "First")
        b = executor.submit(submit, "Changed" if different_content else "First")
        results = [a.result(timeout=20), b.result(timeout=20)]
    successful = [item for item in results if item != "conflict"]
    assert sum(item[1] for item in successful) == 1
    if different_content:
        assert results.count("conflict") == 1
    else:
        assert len(successful) == 2 and successful[0][0] == successful[1][0]
    with psycopg.connect(core_database_url) as observer:
        assert CoreRepository(observer).list_messages(case.id) == [successful[0][0]]
