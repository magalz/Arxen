"""Real HTTP, PostgreSQL, retries and response/commit ordering for conversation."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from threading import Barrier
from uuid import UUID, uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient

from arxen_api.main import create_app
from arxen_api.persistence import CoreRepository

TOKEN = "synthetic-conversation-integration"


def environment(url, owner, token=TOKEN):
    return {
        "ARXEN_ENV": "test",
        "ARXEN_SYNTHETIC_AUTH_ENABLED": "true",
        "ARXEN_SYNTHETIC_USER_ID": str(owner),
        "ARXEN_SYNTHETIC_TOKEN": token,
        "DATABASE_URL": url,
    }


def headers(token=TOKEN):
    return {"Authorization": f"Bearer {token}"}


def prepare_case(url, owner):
    with psycopg.connect(url) as connection:
        return CoreRepository(connection).create_owned_case(owner)


def payload(key=None, content="Synthetic original"):
    return {"client_message_id": str(key or uuid4()), "content": content}


def state(url, case):
    with psycopg.connect(url) as connection:
        return (
            CoreRepository(connection).list_messages(case),
            connection.execute(
                "SELECT message_sequence FROM cases WHERE id=%s", (case,)
            ).fetchone(),
            connection.execute(
                "SELECT client_message_id, message_id, owner_user_id "
                "FROM synthetic_message_submissions WHERE case_id=%s "
                "ORDER BY client_message_id",
                (case,),
            ).fetchall(),
        )


@pytest.mark.parametrize("scheme", ["postgresql://", "postgresql+psycopg://"])
@pytest.mark.parametrize("include_header", [False, True])
def test_submission_survives_recreation_and_reconciles_lost_response(
    core_database_url, scheme, include_header
):
    owner, key = uuid4(), uuid4()
    case = prepare_case(core_database_url, owner)
    path = f"/api/v1/cases/{case.id}/messages"
    url = core_database_url.replace("postgresql://", scheme, 1)
    body = payload(key, "  Conteúdo sintético 🧪\nPreservado. ")
    request_headers = headers() | {"X-User-Id": str(uuid4())}
    if include_header:
        request_headers["Idempotency-Key"] = str(key)
    with TestClient(create_app(environment(url, owner))) as client:
        response = client.post(
            path + f"?owner_user_id={uuid4()}", json=body, headers=request_headers
        )
        assert response.status_code == 201
        message = response.json()
        assert set(message) == {
            "id",
            "case_id",
            "sequence",
            "role",
            "content",
            "created_at",
        }
        assert UUID(message["id"]).version == 4
        assert message["id"] != str(key)
        assert message["case_id"] == str(case.id)
        assert message["role"] == "user"
        assert message["content"] == body["content"]
        assert (
            datetime.fromisoformat(message["created_at"]).utcoffset().total_seconds()
            == 0
        )
        assert response.headers["cache-control"] == "no-store"
    original_state = state(core_database_url, case.id)
    assert original_state[2] == [(key, UUID(message["id"]), owner)]
    rotated = "synthetic-conversation-rotated"
    with TestClient(create_app(environment(url, owner, rotated))) as reopened:
        response = reopened.get(path, headers=headers(rotated))
        assert response.status_code == 200
        assert response.json() == {"items": [message], "next_after_sequence": None}
        replay = reopened.post(path, json=body, headers=headers(rotated))
        assert replay.status_code == 200
        assert replay.json() == message
        conflict = reopened.post(
            path, json=payload(key, "Changed"), headers=headers(rotated)
        )
        assert conflict.status_code == 409
        assert conflict.json() == {"detail": "Message submission conflict"}
        assert reopened.get(path, headers=headers()).status_code == 401
    assert state(core_database_url, case.id) == original_state


def test_other_identity_unknown_and_unassigned_cases_have_identical_denial(
    core_database_url,
):
    owner_a, owner_b = uuid4(), uuid4()
    case_a = prepare_case(core_database_url, owner_a)
    case_b = prepare_case(core_database_url, owner_b)
    key = uuid4()
    with psycopg.connect(core_database_url) as connection:
        internal = CoreRepository(connection).create_case()
    with TestClient(create_app(environment(core_database_url, owner_a))) as a:
        original = a.post(
            f"/api/v1/cases/{case_a.id}/messages", json=payload(key), headers=headers()
        )
        assert original.status_code == 201
    before = state(core_database_url, case_a.id)
    with TestClient(create_app(environment(core_database_url, owner_b))) as b:
        for target in [case_a.id, internal.id, uuid4()]:
            path = f"/api/v1/cases/{target}/messages?user_id={owner_a}"
            for method in ["GET", "POST"]:
                denied = b.request(
                    method,
                    path,
                    json=payload(key, "Different"),
                    headers=headers() | {"X-User-Id": str(owner_a)},
                )
                assert denied.status_code == 404
                assert denied.json() == {"detail": "Case not found"}
                assert denied.headers["cache-control"] == "no-store"
        own = b.post(
            f"/api/v1/cases/{case_b.id}/messages", json=payload(key), headers=headers()
        )
        assert own.status_code == 201
        assert own.json()["id"] != original.json()["id"]
    assert state(core_database_url, case_a.id) == before


def test_history_pages_preserve_order_and_include_internal_legacy_messages(
    core_database_url,
):
    owner = uuid4()
    case = prepare_case(core_database_url, owner)
    path = f"/api/v1/cases/{case.id}/messages"
    with psycopg.connect(core_database_url) as connection:
        legacy = CoreRepository(connection).add_message(
            case.id, "assistant", "Synthetic internal"
        )
    with TestClient(create_app(environment(core_database_url, owner))) as client:
        sent = []
        for content in ["First", "Second", "x" * 16000]:
            response = client.post(
                path, json=payload(content=content), headers=headers()
            )
            assert response.status_code == 201
            sent.append(response.json())
        before = state(core_database_url, case.id)
        first = client.get(path + "?limit=2", headers=headers())
        assert first.status_code == 200
        page = first.json()
        assert [item["id"] for item in page["items"]] == [str(legacy.id), sent[0]["id"]]
        assert page["next_after_sequence"] == sent[0]["sequence"]
        second = client.get(
            path + f"?limit=2&after_sequence={page['next_after_sequence']}",
            headers=headers(),
        )
        assert second.json() == {"items": sent[1:], "next_after_sequence": None}
        end = client.get(
            path + f"?after_sequence={sent[-1]['sequence']}", headers=headers()
        )
        assert end.json() == {"items": [], "next_after_sequence": None}
        assert [
            item["id"] for item in client.get(path, headers=headers()).json()["items"]
        ] == [str(legacy.id)] + [item["id"] for item in sent]
    assert state(core_database_url, case.id) == before


def test_message_and_submission_are_committed_before_success_headers(core_database_url):
    owner, key = uuid4(), uuid4()
    case = prepare_case(core_database_url, owner)
    app = create_app(environment(core_database_url, owner))
    observed = []

    async def probe(scope, receive, send):
        async def inspect(event):
            if event["type"] == "http.response.start" and event["status"] in [200, 201]:
                with psycopg.connect(core_database_url) as connection:
                    observed.append(
                        connection.execute(
                            "SELECT m.id, s.owner_user_id FROM messages m "
                            "JOIN synthetic_message_submissions s "
                            "ON s.case_id=m.case_id AND s.message_id=m.id "
                            "WHERE s.case_id=%s AND s.client_message_id=%s",
                            (case.id, key),
                        ).fetchall()
                    )
            await send(event)

        await app(scope, receive, inspect)

    with TestClient(probe) as client:
        response = client.post(
            f"/api/v1/cases/{case.id}/messages", json=payload(key), headers=headers()
        )
    assert response.status_code == 201
    assert observed == [[(UUID(response.json()["id"]), owner)]]


@pytest.mark.parametrize("failure_time", ["insert", "commit"])
def test_submission_fault_rolls_back_message_counter_and_key(
    core_database_url, failure_time
):
    owner, key = uuid4(), uuid4()
    case = prepare_case(core_database_url, owner)
    function = trigger = "synthetic_submission_fault_" + owner.hex
    with psycopg.connect(core_database_url) as connection:
        assert connection.execute(
            "SELECT to_regclass('public.synthetic_message_submissions')"
        ).fetchone() == ("synthetic_message_submissions",)
        connection.execute(
            psycopg.sql.SQL(
                "CREATE FUNCTION {}() RETURNS trigger LANGUAGE plpgsql AS $$ "
                "BEGIN IF NEW.owner_user_id={}::uuid THEN "
                "RAISE EXCEPTION 'Synthetic submission fault' USING ERRCODE='23514'; "
                "END IF; RETURN NEW; END; $$"
            ).format(psycopg.sql.Identifier(function), psycopg.sql.Literal(owner))
        )
        timing = (
            "CONSTRAINT TRIGGER {} AFTER INSERT ON synthetic_message_submissions "
            "DEFERRABLE INITIALLY DEFERRED"
            if failure_time == "commit"
            else "TRIGGER {} BEFORE INSERT ON synthetic_message_submissions"
        )
        connection.execute(
            psycopg.sql.SQL(
                "CREATE " + timing + " FOR EACH ROW EXECUTE FUNCTION {}()"
            ).format(psycopg.sql.Identifier(trigger), psycopg.sql.Identifier(function))
        )
    path = f"/api/v1/cases/{case.id}/messages"
    try:
        before = state(core_database_url, case.id)
        statuses = []
        app = create_app(environment(core_database_url, owner))

        async def probe(scope, receive, send):
            async def inspect(event):
                if event["type"] == "http.response.start":
                    statuses.append(event["status"])
                await send(event)

            await app(scope, receive, inspect)

        with TestClient(probe, raise_server_exceptions=False) as client:
            response = client.post(path, json=payload(key), headers=headers())
        assert response.status_code == 503
        assert statuses == [503]
        assert response.json() == {"detail": "Case storage unavailable"}
        assert state(core_database_url, case.id) == before
    finally:
        with psycopg.connect(core_database_url) as connection:
            connection.execute(
                psycopg.sql.SQL(
                    "DROP TRIGGER {} ON synthetic_message_submissions"
                ).format(psycopg.sql.Identifier(trigger))
            )
            connection.execute(
                psycopg.sql.SQL("DROP FUNCTION {}()").format(
                    psycopg.sql.Identifier(function)
                )
            )
    with TestClient(create_app(environment(core_database_url, owner))) as client:
        assert (
            client.post(path, json=payload(key), headers=headers()).status_code == 201
        )


@pytest.mark.parametrize("conflicting", [False, True])
def test_concurrent_apps_produce_one_message_for_one_key(
    core_database_url, conflicting
):
    owner, key = uuid4(), uuid4()
    case = prepare_case(core_database_url, owner)
    barrier = Barrier(2)

    def submit(content):
        with TestClient(create_app(environment(core_database_url, owner))) as client:
            barrier.wait(timeout=10)
            return client.post(
                f"/api/v1/cases/{case.id}/messages",
                json=payload(key, content),
                headers=headers(),
            )

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(submit, "Original")
        second = executor.submit(submit, "Changed" if conflicting else "Original")
        results = [first.result(timeout=20), second.result(timeout=20)]
    assert sorted(item.status_code for item in results) == (
        [201, 409] if conflicting else [200, 201]
    )
    successful = next(item for item in results if item.status_code == 201).json()
    stored, counter, submissions = state(core_database_url, case.id)
    assert len(stored) == len(submissions) == 1
    assert counter == (1,)
    assert str(stored[0].id) == successful["id"]


def test_rejected_input_does_not_consume_the_key_or_mutate_history(core_database_url):
    owner, key = uuid4(), uuid4()
    case = prepare_case(core_database_url, owner)
    path = f"/api/v1/cases/{case.id}/messages"
    with TestClient(create_app(environment(core_database_url, owner))) as client:
        invalid = client.post(path, json=payload(key, "  "), headers=headers())
        assert invalid.status_code == 422
        before = state(core_database_url, case.id)
        assert client.post(path, json=payload(key)).status_code == 401
        assert (
            client.post(
                path, json=payload(key) | {"role": "assistant"}, headers=headers()
            ).status_code
            == 422
        )
        assert state(core_database_url, case.id) == before
        assert before == ([], (0,), [])
        assert (
            client.post(path, json=payload(key), headers=headers()).status_code == 201
        )
