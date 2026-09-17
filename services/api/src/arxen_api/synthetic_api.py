"""HTTP entrypoints available only with explicitly enabled synthetic identity."""

from collections.abc import Iterator
from contextlib import contextmanager
from secrets import compare_digest
from typing import Annotated
from uuid import UUID

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field, field_validator

from arxen_api.contracts import Case
from arxen_api.conversation import MessageRepository
from arxen_api.conversation_api import create_conversation_router
from arxen_api.persistence import CoreRepository
from arxen_api.settings import DatabaseSettings
from arxen_api.synthetic_identity import SyntheticIdentity


class SyntheticError(BaseModel):
    """The redacted error body returned by the synthetic HTTP adapter."""

    detail: str


class CaseInput(BaseModel):
    """Only a provisional title is accepted at this stage."""

    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)
    title: str = Field(default="Novo caso", min_length=1, max_length=200)

    @field_validator("title")
    @classmethod
    def valid_title(cls, value: str) -> str:
        if "\x00" in value:
            raise ValueError("Invalid title")
        try:
            value.encode("utf-8")
        except UnicodeEncodeError:
            raise ValueError("Invalid title") from None
        return value


def create_synthetic_router(
    identity: SyntheticIdentity, database: DatabaseSettings
) -> APIRouter:
    router = APIRouter(
        prefix="/api/v1",
        tags=["synthetic development"],
        responses={
            401: {"model": SyntheticError, "description": "Authentication required"}
        },
    )
    bearer = HTTPBearer(auto_error=False, scheme_name="SyntheticBearer")
    database_url = database.database_url.replace(
        "postgresql+psycopg://", "postgresql://", 1
    )

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

    @contextmanager
    def case_connection() -> Iterator[psycopg.Connection[tuple[object, ...]]]:
        # An explicit context finishes commit before a route returns its response.
        try:
            with psycopg.connect(database_url, connect_timeout=5) as connection:
                yield connection
        except psycopg.Error:
            raise HTTPException(
                status_code=503,
                detail="Case storage unavailable",
                headers={"Cache-Control": "no-store"},
            ) from None

    @router.get("/me")
    def me(
        response: Response, user_id: Annotated[UUID, Depends(current_user)]
    ) -> dict[str, UUID | bool]:
        response.headers["Cache-Control"] = "no-store"
        return {"id": user_id, "synthetic": True}

    @router.post(
        "/cases",
        status_code=201,
        responses={
            422: {"model": SyntheticError, "description": "Invalid request"},
            503: {"model": SyntheticError, "description": "Case storage unavailable"},
        },
    )
    def create_case(
        body: CaseInput,
        response: Response,
        user_id: Annotated[UUID, Depends(current_user)],
    ) -> Case:
        with case_connection() as connection:
            case = CoreRepository(connection).create_owned_case(user_id, body.title)
        response.headers["Cache-Control"] = "no-store"
        response.headers["Location"] = f"/api/v1/cases/{case.id}"
        return case

    @router.get(
        "/cases/{case_id}",
        responses={
            404: {"model": SyntheticError, "description": "Case not found"},
            422: {"model": SyntheticError, "description": "Invalid request"},
            503: {"model": SyntheticError, "description": "Case storage unavailable"},
        },
    )
    def get_case(
        case_id: UUID,
        response: Response,
        user_id: Annotated[UUID, Depends(current_user)],
    ) -> Case:
        with case_connection() as connection:
            case = CoreRepository(connection).get_owned_case(user_id, case_id)
        if case is None:
            raise HTTPException(
                status_code=404,
                detail="Case not found",
                headers={"Cache-Control": "no-store"},
            )
        response.headers["Cache-Control"] = "no-store"
        return case

    @contextmanager
    def conversation_repository() -> Iterator[MessageRepository]:
        with case_connection() as connection:
            yield CoreRepository(connection)

    router.include_router(
        create_conversation_router(current_user, conversation_repository)
    )
    return router
