"""Synthetic access is opt-in, credentialed and derived from the server."""

import pytest
from fastapi.testclient import TestClient

from arxen_api.main import create_app
from arxen_api.settings import ConfigurationError

USER_ID = "c921ed2b-747f-47ec-b16d-4ba620190d73"
TOKEN = "synthetic-http-test-token"


def environment() -> dict[str, str]:
    return {
        "ARXEN_ENV": "test",
        "ARXEN_SYNTHETIC_AUTH_ENABLED": "true",
        "ARXEN_SYNTHETIC_USER_ID": USER_ID,
        "ARXEN_SYNTHETIC_TOKEN": TOKEN,
        "DATABASE_URL": "postgresql://example.invalid/synthetic",
    }


def test_server_identity_is_returned_and_caller_identity_header_is_ignored() -> None:
    with TestClient(create_app(environment())) as client:
        response = client.get(
            "/api/v1/me",
            headers={"Authorization": f"Bearer {TOKEN}", "X-User-Id": "someone-else"},
        )
    assert response.status_code == 200
    assert response.json() == {"id": USER_ID, "synthetic": True}
    assert response.headers["cache-control"] == "no-store"
    assert TOKEN not in response.text


@pytest.mark.parametrize(
    "headers",
    [{}, {"Authorization": "Bearer wrong"}, {"Authorization": "Basic irrelevant"}],
)
def test_missing_or_wrong_credential_receives_same_unauthorized_response(
    headers,
) -> None:
    with TestClient(create_app(environment())) as client:
        response = client.get("/api/v1/me", headers=headers)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json() == {"detail": "Authentication required"}
    assert TOKEN not in response.text


def test_mode_is_absent_from_default_application_and_openapi() -> None:
    with TestClient(create_app({})) as client:
        assert client.get("/api/v1/me").status_code == 404
        assert "/api/v1/me" not in client.get("/openapi.json").json()["paths"]


def test_enabled_openapi_declares_bearer_without_embedding_credentials() -> None:
    with TestClient(create_app(environment())) as client:
        response = client.get("/openapi.json")
    schema = response.json()
    assert "/api/v1/me" in schema["paths"]
    assert schema["paths"]["/api/v1/me"]["get"]["security"]
    assert any(
        scheme.get("type") == "http" and scheme.get("scheme") == "bearer"
        for scheme in schema["components"]["securitySchemes"].values()
    )
    assert TOKEN not in response.text


def test_enabled_health_check_does_not_connect_to_database() -> None:
    with TestClient(create_app(environment())) as client:
        assert client.get("/healthz").json() == {
            "status": "ok",
            "service": "arxen-api",
        }


def test_application_rejects_synthetic_mode_in_production() -> None:
    with pytest.raises(ConfigurationError, match="development or test"):
        create_app(environment() | {"ARXEN_ENV": "production"})


def test_enabled_application_requires_database_configuration() -> None:
    settings = environment()
    del settings["DATABASE_URL"]
    with pytest.raises(ConfigurationError, match="DATABASE_URL"):
        create_app(settings)
