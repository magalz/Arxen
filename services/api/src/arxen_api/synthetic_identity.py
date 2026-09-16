"""Opt-in identity for synthetic development and integration exercises."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from uuid import UUID

from arxen_api.settings import ConfigurationError


@dataclass(frozen=True)
class SyntheticIdentity:
    user_id: UUID
    token: str = field(repr=False)


def load_synthetic_identity(environ: Mapping[str, str]) -> SyntheticIdentity | None:
    """Return the explicitly configured test identity, or leave the mode disabled."""
    enabled = environ.get("ARXEN_SYNTHETIC_AUTH_ENABLED", "false").strip().lower()
    if enabled not in {"true", "false"}:
        raise ConfigurationError("ARXEN_SYNTHETIC_AUTH_ENABLED must be true or false")
    if enabled == "false":
        return None
    if environ.get("ARXEN_ENV") not in {"development", "test"}:
        raise ConfigurationError("Synthetic identity requires development or test")

    try:
        user_id = UUID(environ.get("ARXEN_SYNTHETIC_USER_ID", ""))
    except ValueError:
        raise ConfigurationError(
            "ARXEN_SYNTHETIC_USER_ID must be a nonzero UUID"
        ) from None
    if user_id.int == 0:
        raise ConfigurationError("ARXEN_SYNTHETIC_USER_ID must be a nonzero UUID")

    token = environ.get("ARXEN_SYNTHETIC_TOKEN", "")
    if not token or any(character.isspace() for character in token):
        raise ConfigurationError(
            "ARXEN_SYNTHETIC_TOKEN must be nonempty without spaces"
        )
    return SyntheticIdentity(user_id=user_id, token=token)
