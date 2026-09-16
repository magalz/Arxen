"""ASGI application entrypoint."""

from fastapi import FastAPI


def create_app() -> FastAPI:
    """Create an independent application instance."""
    application = FastAPI()

    @application.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok", "service": "arxen-api"}

    return application


app = create_app()
