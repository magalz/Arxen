"""HTTP conversation adapter using server identity and caller-owned transactions."""

from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator

from arxen_api.contracts import Message
from arxen_api.conversation import MessageConflict, MessageRepository


class ConversationError(BaseModel):
    detail: str


class MessageInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    client_message_id: UUID = Field(strict=False)
    content: str = Field(min_length=1, max_length=16000)

    @field_validator("client_message_id")
    @classmethod
    def nonzero_key(cls, value: UUID) -> UUID:
        if value.int == 0:
            raise ValueError("Invalid submission identifier")
        return value

    @field_validator("content")
    @classmethod
    def valid_text(cls, value: str) -> str:
        if not value.strip() or "\x00" in value:
            raise ValueError("Invalid message content")
        try:
            value.encode("utf-8")
        except UnicodeEncodeError:
            raise ValueError("Invalid message content") from None
        return value


class MessagePage(BaseModel):
    items: list[Message]
    next_after_sequence: int | None


def conversation_error(status: int, detail: str) -> HTTPException:
    return HTTPException(
        status_code=status, detail=detail, headers={"Cache-Control": "no-store"}
    )


def create_conversation_router(
    current_user: Callable[..., UUID],
    repository: Callable[[], AbstractContextManager[MessageRepository]],
) -> APIRouter:
    router = APIRouter(
        responses={
            401: {"model": ConversationError, "description": "Authentication required"},
            404: {"model": ConversationError, "description": "Case not found"},
            422: {"model": ConversationError, "description": "Invalid request"},
            503: {
                "model": ConversationError,
                "description": "Case storage unavailable",
            },
        }
    )

    @router.post(
        "/cases/{case_id}/messages",
        status_code=201,
        responses={
            200: {"model": Message, "description": "Existing submission"},
            409: {
                "model": ConversationError,
                "description": "Message submission conflict",
            },
        },
    )
    def submit_message(
        case_id: UUID,
        body: MessageInput,
        response: Response,
        user_id: Annotated[UUID, Depends(current_user)],
        idempotency_key: Annotated[UUID | None, Header()] = None,
    ) -> Message:
        if idempotency_key is not None and idempotency_key != body.client_message_id:
            raise conversation_error(422, "Invalid request")
        try:
            with repository() as store:
                result = store.submit_owned_message(
                    user_id, case_id, body.client_message_id, body.content
                )
        except MessageConflict:
            raise conversation_error(409, "Message submission conflict") from None
        if result is None:
            raise conversation_error(404, "Case not found")
        message, created = result
        response.status_code = 201 if created else 200
        response.headers["Cache-Control"] = "no-store"
        return message

    @router.get("/cases/{case_id}/messages")
    def history(
        case_id: UUID,
        response: Response,
        user_id: Annotated[UUID, Depends(current_user)],
        after_sequence: Annotated[int, Query(ge=0, le=9223372036854775807)] = 0,
        limit: Annotated[int, Query(ge=1, le=100)] = 50,
    ) -> MessagePage:
        with repository() as store:
            messages = store.list_owned_messages(
                user_id, case_id, after_sequence=after_sequence, limit=limit + 1
            )
        if messages is None:
            raise conversation_error(404, "Case not found")
        response.headers["Cache-Control"] = "no-store"
        return MessagePage(
            items=messages[:limit],
            next_after_sequence=messages[limit - 1].sequence
            if len(messages) > limit
            else None,
        )

    return router
