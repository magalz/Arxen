"""ASGI application entrypoint."""

import os
from collections.abc import Mapping

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from arxen_api.settings import load_database_settings
from arxen_api.synthetic_api import create_synthetic_router
from arxen_api.synthetic_identity import load_synthetic_identity


def create_app(environ: Mapping[str, str] | None = None) -> FastAPI:
    """Create an independent application instance."""
    application = FastAPI()

    @application.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok", "service": "arxen-api"}

    configured = os.environ if environ is None else environ
    identity = load_synthetic_identity(configured)
    if identity is not None:
        database = load_database_settings(configured)

        @application.exception_handler(RequestValidationError)
        async def invalid_request(
            request: Request, error: RequestValidationError
        ) -> JSONResponse:
            # Validation details may contain submitted credentials or private input.
            return JSONResponse(
                status_code=422,
                content={"detail": "Invalid request"},
                headers={"Cache-Control": "no-store"},
            )

        application.include_router(create_synthetic_router(identity, database))

    return application


app = create_app()
