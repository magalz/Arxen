"""ASGI application entrypoint."""

from collections.abc import Mapping

from fastapi import FastAPI


def create_app(environ: Mapping[str, str] | None = None) -> FastAPI:
    """Create an independent application instance."""
    application = FastAPI()

    @application.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok", "service": "arxen-api"}

    return application


app = create_app()
