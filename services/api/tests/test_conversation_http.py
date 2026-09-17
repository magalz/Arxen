"""Conversation authentication, strict validation and published HTTP contracts."""

from uuid import uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient

from arxen_api.main import create_app

OWNER = "7e282b02-088f-4802-8b83-d0b489481b83"
TOKEN = "synthetic-conversation-token"
CASE = "dcdf52e0-7c15-4a8f-8a2f-79d3a70bcfb6"
PATH = f"/api/v1/cases/{CASE}/messages"
KEY = "d7d363cb-08c6-4cae-8d6a-179e2abaf54f"


def environment():
    return {
        "ARXEN_ENV": "test",
        "ARXEN_SYNTHETIC_AUTH_ENABLED": "true",
        "ARXEN_SYNTHETIC_USER_ID": OWNER,
        "ARXEN_SYNTHETIC_TOKEN": TOKEN,
        "DATABASE_URL": "postgresql://example.invalid/synthetic",
    }


@pytest.fixture
def client(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Invalid or unauthenticated request opened a database")

    monkeypatch.setattr(psycopg, "connect", forbidden)
    with TestClient(create_app(environment())) as instance:
        yield instance


def headers():
    return {"Authorization": f"Bearer {TOKEN}"}


@pytest.mark.parametrize("method", ["GET", "POST"])
def test_conversation_is_absent_when_mode_is_disabled(method):
    with TestClient(create_app({})) as instance:
        assert instance.request(method, PATH, json={}).status_code == 404
        assert (
            "/api/v1/cases/{case_id}/messages"
            not in instance.get("/openapi.json").json()["paths"]
        )


@pytest.mark.parametrize("method", ["GET", "POST"])
@pytest.mark.parametrize(
    "credential",
    [
        {},
        {"Authorization": "Bearer wrong"},
        {"Authorization": "Basic ignored"},
        {"X-User-Id": OWNER},
    ],
)
def test_bearer_required_before_storage(client, method, credential):
    response = client.request(
        method,
        PATH,
        json={"client_message_id": KEY, "content": "Synthetic"},
        headers=credential,
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize(
    "content",
    [None, 1, True, [], {}, "", " \t\n ", "x" * 16001, "bad\x00text", "bad\ud800text"],
)
def test_invalid_text_is_rejected_without_echo_or_database(client, content):
    import json

    response = client.post(
        PATH,
        content=json.dumps({"client_message_id": KEY, "content": content}),
        headers=headers() | {"Content-Type": "application/json"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid request"}
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize(
    "key", [None, "", "bad", 42, True, {}, "00000000-0000-0000-0000-000000000000"]
)
def test_invalid_submission_id_is_rejected(client, key):
    response = client.post(
        PATH, json={"client_message_id": key, "content": "Synthetic"}, headers=headers()
    )
    assert response.status_code == 422


@pytest.mark.parametrize(
    "field",
    [
        "role",
        "owner_user_id",
        "user_id",
        "id",
        "sequence",
        "created_at",
        "task_id",
        "attachments",
        "token",
    ],
)
def test_client_cannot_set_server_fields_or_future_capabilities(client, field):
    response = client.post(
        PATH,
        json={"client_message_id": KEY, "content": "Synthetic", field: TOKEN},
        headers=headers(),
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid request"}
    assert TOKEN not in response.text


@pytest.mark.parametrize(
    "payload", [{}, {"content": "Synthetic"}, {"client_message_id": KEY}, [], None]
)
def test_required_message_body_is_explicit(client, payload):
    assert client.post(PATH, json=payload, headers=headers()).status_code == 422


@pytest.mark.parametrize(
    "key", ["bad", "", str(uuid4()), "00000000-0000-0000-0000-000000000000"]
)
def test_optional_idempotency_header_must_identify_the_same_submission(client, key):
    response = client.post(
        PATH,
        json={"client_message_id": KEY, "content": "Synthetic"},
        headers=headers() | {"Idempotency-Key": key},
    )
    assert response.status_code == 422
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize(
    "query",
    [
        "limit=0",
        "limit=101",
        "limit=1.5",
        "limit=bad",
        "after_sequence=-1",
        "after_sequence=1.5",
        "after_sequence=bad",
        "after_sequence=9223372036854775808",
    ],
)
def test_invalid_history_bounds_are_rejected_before_database(client, query):
    assert client.get(f"{PATH}?{query}", headers=headers()).status_code == 422


@pytest.mark.parametrize("method", ["GET", "POST"])
def test_malformed_case_id_does_not_reach_database(client, method):
    response = client.request(
        method,
        "/api/v1/cases/not-a-uuid/messages",
        json={"client_message_id": KEY, "content": "Synthetic"},
        headers=headers(),
    )
    assert response.status_code == 422


@pytest.mark.parametrize("method", ["GET", "POST"])
def test_storage_failure_remains_sanitized(monkeypatch, method):
    def unavailable(*args, **kwargs):
        raise psycopg.OperationalError("private connection diagnostic")

    monkeypatch.setattr(psycopg, "connect", unavailable)
    with TestClient(create_app(environment())) as instance:
        response = instance.request(
            method,
            PATH,
            json={"client_message_id": KEY, "content": "Synthetic"},
            headers=headers(),
        )
    assert response.status_code == 503
    assert response.json() == {"detail": "Case storage unavailable"}
    assert response.headers["cache-control"] == "no-store"
    assert "diagnostic" not in response.text


def test_openapi_describes_content_cursor_auth_and_real_error_bodies(client):
    schema = client.get("/openapi.json").json()
    route = schema["paths"].get("/api/v1/cases/{case_id}/messages")
    assert route is not None, "Conversation HTTP contract is absent"
    for method in ["post", "get"]:
        assert route[method]["security"]
        for status in ["401", "404", "422", "503"] + (
            ["409"] if method == "post" else []
        ):
            body = route[method]["responses"][status]["content"]["application/json"][
                "schema"
            ]
            if "$ref" in body:
                body = schema["components"]["schemas"][body["$ref"].split("/")[-1]]
            assert body["properties"]["detail"]["type"] == "string"
    assert {"200", "201"} <= route["post"]["responses"].keys()
    body = route["post"]["requestBody"]["content"]["application/json"]["schema"]
    body = schema["components"]["schemas"][body["$ref"].split("/")[-1]]
    assert body["additionalProperties"] is False
    assert set(body["properties"]) == {"client_message_id", "content"}
    assert set(body["required"]) == {"client_message_id", "content"}
    assert TOKEN not in str(schema)
