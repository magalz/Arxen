"""Request validation and failures must not expose credentials or access storage."""

import psycopg
import pytest
from fastapi.testclient import TestClient

from arxen_api.main import create_app

USER_ID = "d9d02a60-7970-4fd8-abca-25318f3c4e80"
OTHER_ID = "378460e2-0610-45d9-8c03-4b2b12153f84"
TOKEN = "synthetic-case-http-token"
CASE_PATH = f"/api/v1/cases/{OTHER_ID}"


def environment() -> dict[str, str]:
    return {
        "ARXEN_ENV": "test",
        "ARXEN_SYNTHETIC_AUTH_ENABLED": "true",
        "ARXEN_SYNTHETIC_USER_ID": USER_ID,
        "ARXEN_SYNTHETIC_TOKEN": TOKEN,
        "DATABASE_URL": "postgresql://example.invalid/synthetic",
    }


@pytest.fixture
def no_database(monkeypatch) -> None:
    def forbid_connection(*args, **kwargs):
        pytest.fail(
            "This request must be rejected before opening a database connection"
        )

    monkeypatch.setattr(psycopg, "connect", forbid_connection)


@pytest.mark.parametrize("method,path", [("POST", "/api/v1/cases"), ("GET", CASE_PATH)])
def test_case_routes_are_absent_when_synthetic_mode_is_disabled(
    no_database, method, path
) -> None:
    with TestClient(create_app({})) as client:
        assert client.request(method, path, json={}).status_code == 404
        paths = client.get("/openapi.json").json()["paths"]
        assert "/api/v1/cases" not in paths
        assert "/api/v1/cases/{case_id}" not in paths


@pytest.mark.parametrize("method,path", [("POST", "/api/v1/cases"), ("GET", CASE_PATH)])
@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"Authorization": "Bearer incorrect"},
        {"Authorization": "Basic irrelevant"},
        {"X-User-Id": USER_ID},
    ],
)
def test_case_requests_require_bearer_before_database(
    no_database, method, path, headers
) -> None:
    with TestClient(create_app(environment())) as client:
        response = client.request(method, path, json={}, headers=headers)
    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.headers["cache-control"] == "no-store"
    assert TOKEN not in response.text


@pytest.mark.parametrize(
    "payload",
    [
        {"owner_user_id": OTHER_ID},
        {"user_id": OTHER_ID},
        {"id": OTHER_ID},
        {"created_at": "2026-01-01T00:00:00Z"},
        {"unknown": "synthetic"},
        {"title": None},
        {"title": ""},
        {"title": " \t\n "},
        {"title": 42},
        {"title": True},
        {"title": []},
        {"title": {}},
        {"title": "x" * 201},
        {"title": "invalid\x00title"},
        [],
    ],
)
def test_invalid_case_input_is_rejected_without_database(no_database, payload) -> None:
    with TestClient(create_app(environment())) as client:
        response = client.post(
            "/api/v1/cases", json=payload, headers={"Authorization": f"Bearer {TOKEN}"}
        )
    assert response.status_code == 422
    assert TOKEN not in response.text


def test_missing_body_and_malformed_case_id_do_not_open_database(no_database) -> None:
    with TestClient(create_app(environment())) as client:
        headers = {"Authorization": f"Bearer {TOKEN}"}
        assert client.post("/api/v1/cases", headers=headers).status_code == 422
        assert (
            client.get("/api/v1/cases/not-a-uuid", headers=headers).status_code == 422
        )


@pytest.mark.parametrize("method,path", [("POST", "/api/v1/cases"), ("GET", CASE_PATH)])
def test_storage_failure_is_generic_and_never_success(
    monkeypatch, method, path
) -> None:
    diagnostic = "synthetic-database-diagnostic-not-for-http"

    def unavailable(*args, **kwargs):
        raise psycopg.OperationalError(diagnostic)

    monkeypatch.setattr(psycopg, "connect", unavailable)
    with TestClient(create_app(environment())) as client:
        response = client.request(
            method, path, json={}, headers={"Authorization": f"Bearer {TOKEN}"}
        )
    assert response.status_code == 503
    assert response.json() == {"detail": "Case storage unavailable"}
    assert response.headers["cache-control"] == "no-store"
    assert diagnostic not in response.text
    assert TOKEN not in response.text


def test_case_openapi_declares_authentication_and_only_the_admitted_input(
    no_database,
) -> None:
    with TestClient(create_app(environment())) as client:
        response = client.get("/openapi.json")
    schema = response.json()
    create = schema["paths"].get("/api/v1/cases", {}).get("post")
    read = schema["paths"].get("/api/v1/cases/{case_id}", {}).get("get")
    assert create is not None, "The authenticated case creation contract is missing"
    assert read is not None, "The authenticated case read contract is missing"
    assert create["security"] and read["security"]
    body_ref = create["requestBody"]["content"]["application/json"]["schema"]["$ref"]
    body = schema["components"]["schemas"][body_ref.rsplit("/", 1)[-1]]
    assert body["additionalProperties"] is False
    assert set(body["properties"]) == {"title"}
    assert body["properties"]["title"]["default"] == "Novo caso"
    assert "201" in create["responses"]
    assert TOKEN not in response.text
