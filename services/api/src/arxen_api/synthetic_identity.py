"""Opt-in identity for synthetic development and integration exercises."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from uuid import UUID


@dataclass(frozen=True)
class SyntheticIdentity:
    user_id: UUID
    token: str = field(repr=False)


def load_synthetic_identity(environ: Mapping[str, str]) -> SyntheticIdentity | None:
    """Return the explicitly configured test identity, or leave the mode disabled."""
    return None
