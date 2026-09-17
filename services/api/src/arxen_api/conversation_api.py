"""HTTP conversation adapter using server identity and caller-owned transactions."""

from collections.abc import Callable
from contextlib import AbstractContextManager
from uuid import UUID

from fastapi import APIRouter

from arxen_api.conversation import MessageRepository


def create_conversation_router(
    current_user: Callable[..., UUID],
    repository: Callable[[], AbstractContextManager[MessageRepository]],
) -> APIRouter:
    return APIRouter()
