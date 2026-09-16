"""Invalid input cannot echo credentials or reach the database."""

import psycopg
import pytest
from fastapi.testclient import TestClient

from arxen_api.main import create_app

TOKEN = "synthetic-request-privacy-token"
USER_ID = "6c94e3b8-b8a7-453a-9d68-7d10a6473a45"


@pytest.fixture
def client(monkeypatch):
    def forbid_connection(*args, **kwargs):
        pytest.fail("Invalid input reached database connection creation")

    monkeypatch.setattr(psycopg, "connect", forbid_connection)
    settings = {
        "ARXEN_ENV": "test",
        "ARXEN_SYNTHETIC_AUTH_ENABLED": "true",
        "ARXEN_SYNTHETIC_USER_ID": USER_ID,
        "ARXEN_SYNTHETIC_TOKEN": TOKEN,
        "DATABASE_URL": "postgresql://example.invalid/synthetic",
    }
    with TestClient(create_app(settings)) as test_client:
        yield test_client


@pytest.mark.parametrize("payload", [{"token": TOKEN}, {"title": {"secret": TOKEN}}])
def test_validation_errors_do_not_reflect_submitted_secrets(client, payload) -> None:
    response = client.post(
        "/api/v1/cases", json=payload, headers={"Authorization": f"Bearer {TOKEN}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid request"}
    assert response.headers["cache-control"] == "no-store"
    assert TOKEN not in response.text


def test_non_utf8_title_is_rejected_without_reflecting_it(client) -> None:
    response = client.post(
        "/api/v1/cases",
        content='{"title": "\\ud800"}',
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
        },
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid request"}


def test_token_in_body_or_query_is_not_a_bearer_credential(client) -> None:
    response = client.post(
        f"/api/v1/cases?token={TOKEN}&user_id={USER_ID}",
        json={"token": TOKEN},
        headers={"X-User-Id": USER_ID},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}
    assert TOKEN not in response.text
