"""Boundaries for durable synthetic message submission."""

from typing import Protocol
from uuid import UUID

from arxen_api.contracts import Message


class MessageConflict(ValueError):
    """An existing submission key identifies different immutable content."""


class MessageRepository(Protocol):
    def submit_owned_message(
        self, owner_user_id: UUID, case_id: UUID, client_message_id: UUID, content: str
    ) -> tuple[Message, bool] | None: ...

    def list_owned_messages(
        self, owner_user_id: UUID, case_id: UUID, *, after_sequence: int, limit: int
    ) -> list[Message] | None: ...
