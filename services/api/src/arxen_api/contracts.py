"""Internal persisted records; these types do not grant access to a case."""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID


@dataclass(frozen=True, kw_only=True)
class StoredRecord:
    """Server-generated identity and operational timestamp."""

    id: UUID
    created_at: datetime

    def __post_init__(self) -> None:
        if self.created_at.utcoffset() is None:
            raise ValueError("created_at must have a timezone")
        object.__setattr__(self, "created_at", self.created_at.astimezone(UTC))


@dataclass(frozen=True, kw_only=True)
class Case(StoredRecord):
    title: str


type MessageRole = Literal["user", "assistant"]


@dataclass(frozen=True, kw_only=True)
class Message(StoredRecord):
    case_id: UUID
    sequence: int
    role: MessageRole
    content: str
