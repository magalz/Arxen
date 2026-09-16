"""Public health contract through both supported application entrypoints."""

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from arxen_api.main import app, create_app


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(params=["factory", "asgi-entrypoint"])
def application(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> FastAPI:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    return create_app() if request.param == "factory" else app


@pytest.mark.anyio
async def test_healthz_returns_json_contract_without_database(
    application: FastAPI,
) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=application), base_url="http://arxen.test"
    ) as client:
        response = await client.get("/healthz")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json() == {"status": "ok", "service": "arxen-api"}
