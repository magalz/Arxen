"""HTTP entrypoints available only with explicitly enabled synthetic identity."""

from secrets import compare_digest
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from arxen_api.synthetic_identity import SyntheticIdentity


def create_synthetic_router(identity: SyntheticIdentity) -> APIRouter:
    router = APIRouter(prefix="/api/v1", tags=["synthetic development"])
    bearer = HTTPBearer(auto_error=False, scheme_name="SyntheticBearer")

    def current_user(
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    ) -> UUID:
        if credentials is None or not compare_digest(
            credentials.credentials.encode("utf-8"), identity.token.encode("utf-8")
        ):
            raise HTTPException(
                status_code=401,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer", "Cache-Control": "no-store"},
            )
        return identity.user_id

    @router.get("/me")
    def me(
        response: Response, user_id: Annotated[UUID, Depends(current_user)]
    ) -> dict[str, UUID | bool]:
        response.headers["Cache-Control"] = "no-store"
        return {"id": user_id, "synthetic": True}

    return router
