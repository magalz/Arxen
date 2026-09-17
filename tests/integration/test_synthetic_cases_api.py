"""Real HTTP wiring, durable ownership and transaction boundaries in PostgreSQL."""

from datetime import datetime
from uuid import UUID, uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient

from arxen_api.main import create_app
from arxen_api.persistence import CoreRepository

USER_A = "433a1990-222f-43bb-ae94-ae9b24245cb8"
USER_B = "b1cf7b86-481b-4571-842e-dfd45fdfd041"
TOKEN_A = "synthetic-api-token-a"
TOKEN_B = "synthetic-api-token-b"


def environment(database_url, user=USER_A, token=TOKEN_A):
    return {
        "ARXEN_ENV": "test",
        "ARXEN_SYNTHETIC_AUTH_ENABLED": "true",
        "ARXEN_SYNTHETIC_USER_ID": user,
        "ARXEN_SYNTHETIC_TOKEN": token,
        "DATABASE_URL": database_url,
    }


def headers(token=TOKEN_A):
    return {"Authorization": f"Bearer {token}"}


def counts(database_url):
    with psycopg.connect(database_url) as connection:
        return connection.execute(
            "SELECT (SELECT count(*) FROM cases), "
            "(SELECT count(*) FROM synthetic_case_owners)"
        ).fetchone()


@pytest.mark.parametrize(
    "payload,expected_title",
    [
        ({}, "Novo caso"),
        ({"title": "  Caso sintético ç 漢字  "}, "Caso sintético ç 漢字"),
    ],
)
@pytest.mark.parametrize("scheme", ["postgresql://", "postgresql+psycopg://"])
def test_creation_persists_server_identity_and_reopens_after_application_recreation(
    core_database_url, payload, expected_title, scheme
) -> None:
    url = core_database_url.replace("postgresql://", scheme, 1)
    with TestClient(create_app(environment(url))) as client:
        response = client.post(
            f"/api/v1/cases?owner_user_id={USER_B}&user_id={USER_B}",
            json=payload,
            headers=headers() | {"X-User-Id": USER_B},
        )
        assert response.status_code == 201
        case = response.json()
        assert set(case) == {"id", "title", "created_at"}
        assert UUID(case["id"]).version == 4
        assert case["title"] == expected_title
        assert (
            datetime.fromisoformat(case["created_at"]).utcoffset().total_seconds() == 0
        )
        assert response.headers["cache-control"] == "no-store"
        assert response.headers["location"] == f"/api/v1/cases/{case['id']}"

        with psycopg.connect(core_database_url) as observer:
            stored = CoreRepository(observer).get_case(UUID(case["id"]))
            assert stored is not None
            assert stored.title == expected_title
            assert stored.created_at == datetime.fromisoformat(case["created_at"])
            assert observer.execute(
                "SELECT owner_user_id FROM synthetic_case_owners WHERE case_id = %s",
                (case["id"],),
            ).fetchone() == (UUID(USER_A),)

        before = counts(core_database_url)
        first = client.get(f"/api/v1/cases/{case['id']}", headers=headers())
        assert first.status_code == 200
        assert first.json() == case
        assert first.headers["cache-control"] == "no-store"

    # The binding follows the stable user UUID, not a token or application memory.
    new_token = "synthetic-rotated-token"
    with TestClient(create_app(environment(url, token=new_token))) as reopened:
        for _ in range(2):
            response = reopened.get(
                f"/api/v1/cases/{case['id']}", headers=headers(new_token)
            )
            assert response.status_code == 200
            assert response.json() == case
        assert (
            reopened.get(f"/api/v1/cases/{case['id']}", headers=headers()).status_code
            == 401
        )
    assert counts(core_database_url) == before


def test_two_identities_cannot_read_each_others_cases_or_unassigned_cases(
    core_database_url,
) -> None:
    with psycopg.connect(core_database_url) as connection:
        unassigned = CoreRepository(connection).create_case("Synthetic internal case")

    with (
        TestClient(create_app(environment(core_database_url))) as client_a,
        TestClient(
            create_app(environment(core_database_url, USER_B, TOKEN_B))
        ) as client_b,
    ):
        response_a = client_a.post("/api/v1/cases", json={}, headers=headers())
        response_b = client_b.post("/api/v1/cases", json={}, headers=headers(TOKEN_B))
        assert response_a.status_code == response_b.status_code == 201
        case_a = response_a.json()
        case_b = response_b.json()
        assert case_a["id"] != case_b["id"]
        before = counts(core_database_url)

        for client, token, other_case, spoofed_user in [
            (client_a, TOKEN_A, case_b, USER_B),
            (client_b, TOKEN_B, case_a, USER_A),
        ]:
            denied = []
            for case_id in [other_case["id"], str(unassigned.id), str(uuid4())]:
                response = client.get(
                    f"/api/v1/cases/{case_id}?owner_user_id={spoofed_user}",
                    headers=headers(token) | {"X-User-Id": spoofed_user},
                )
                assert response.status_code == 404
                assert response.headers["cache-control"] == "no-store"
                denied.append(response.json())
            assert denied == [{"detail": "Case not found"}] * 3

        assert (
            client_a.get(f"/api/v1/cases/{case_a['id']}", headers=headers()).json()
            == case_a
        )
        assert (
            client_b.get(
                f"/api/v1/cases/{case_b['id']}", headers=headers(TOKEN_B)
            ).json()
            == case_b
        )
    assert counts(core_database_url) == before


def test_case_is_committed_before_the_success_headers_are_sent(
    core_database_url,
) -> None:
    title = f"Synthetic commit probe {uuid4()}"
    application = create_app(environment(core_database_url))
    observed = []

    async def probe(scope, receive, send):
        async def inspect_send(message):
            if message["type"] == "http.response.start" and message["status"] == 201:
                with psycopg.connect(core_database_url) as observer:
                    observed.extend(
                        observer.execute(
                            "SELECT c.id, o.owner_user_id FROM cases c "
                            "JOIN synthetic_case_owners o ON o.case_id = c.id "
                            "WHERE c.title = %s",
                            (title,),
                        ).fetchall()
                    )
            await send(message)

        await application(scope, receive, inspect_send)

    with TestClient(probe) as client:
        response = client.post(
            "/api/v1/cases", json={"title": title}, headers=headers()
        )
    assert response.status_code == 201
    assert observed == [(UUID(response.json()["id"]), UUID(USER_A))]


@pytest.mark.parametrize("failure_time", ["insert", "commit"])
def test_binding_failure_never_sends_success_and_rolls_back_the_case(
    core_database_url, failure_time
) -> None:
    # A unique configured identity confines this fault to this request.
    failing_user = uuid4()
    suffix = failing_user.hex
    function = f"synthetic_failure_{suffix}"
    trigger = f"synthetic_failure_{suffix}"
    with psycopg.connect(core_database_url) as connection:
        assert connection.execute(
            "SELECT to_regclass('public.synthetic_case_owners')"
        ).fetchone() == ("synthetic_case_owners",)
        connection.execute(
            psycopg.sql.SQL(
                "CREATE FUNCTION {}() RETURNS trigger LANGUAGE plpgsql AS $$ "
                "BEGIN IF NEW.owner_user_id = {}::uuid THEN "
                "RAISE EXCEPTION 'Synthetic binding fault' USING ERRCODE = '23514'; "
                "END IF; RETURN NEW; END; $$"
            ).format(
                psycopg.sql.Identifier(function), psycopg.sql.Literal(failing_user)
            )
        )
        timing = (
            "CONSTRAINT TRIGGER {} AFTER INSERT ON synthetic_case_owners "
            "DEFERRABLE INITIALLY DEFERRED"
            if failure_time == "commit"
            else "TRIGGER {} BEFORE INSERT ON synthetic_case_owners"
        )
        connection.execute(
            psycopg.sql.SQL(
                "CREATE " + timing + " FOR EACH ROW EXECUTE FUNCTION {}()"
            ).format(psycopg.sql.Identifier(trigger), psycopg.sql.Identifier(function))
        )

    try:
        before = counts(core_database_url)
        application = create_app(environment(core_database_url, str(failing_user)))
        sent_statuses = []

        async def probe(scope, receive, send):
            async def inspect_send(message):
                if message["type"] == "http.response.start":
                    sent_statuses.append(message["status"])
                await send(message)

            await application(scope, receive, inspect_send)

        with TestClient(probe, raise_server_exceptions=False) as client:
            response = client.post("/api/v1/cases", json={}, headers=headers())
        assert response.status_code == 503
        assert response.json() == {"detail": "Case storage unavailable"}
        assert sent_statuses == [503]
        assert "Synthetic binding fault" not in response.text
        assert counts(core_database_url) == before
    finally:
        with psycopg.connect(core_database_url) as connection:
            connection.execute(
                psycopg.sql.SQL("DROP TRIGGER {} ON synthetic_case_owners").format(
                    psycopg.sql.Identifier(trigger)
                )
            )
            connection.execute(
                psycopg.sql.SQL("DROP FUNCTION {}()").format(
                    psycopg.sql.Identifier(function)
                )
            )


def test_invalid_requests_leave_no_partial_rows(core_database_url) -> None:
    with psycopg.connect(core_database_url) as connection:
        assert connection.execute(
            "SELECT to_regclass('public.synthetic_case_owners')"
        ).fetchone() == ("synthetic_case_owners",)
    before = counts(core_database_url)
    with TestClient(create_app(environment(core_database_url))) as client:
        for payload in [{"owner_user_id": USER_B}, {"title": " "}, {"title": 7}]:
            assert (
                client.post(
                    "/api/v1/cases", json=payload, headers=headers()
                ).status_code
                == 422
            )
        assert client.post("/api/v1/cases", json={}).status_code == 401
        assert (
            client.post("/api/v1/cases", json={}, headers=headers("wrong")).status_code
            == 401
        )
    assert counts(core_database_url) == before
