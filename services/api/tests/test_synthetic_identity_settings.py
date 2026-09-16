"""Synthetic credentials require explicit opt-in and a non-production environment."""

from uuid import UUID

import pytest

from arxen_api.settings import ConfigurationError
from arxen_api.synthetic_identity import load_synthetic_identity

USER_ID = "81086fa4-4e8d-46f9-9c63-9b6b0649f205"
TOKEN = "synthetic-test-token-not-a-production-secret"


def enabled_environment() -> dict[str, str]:
    return {
        "ARXEN_ENV": "test",
        "ARXEN_SYNTHETIC_AUTH_ENABLED": "true",
        "ARXEN_SYNTHETIC_USER_ID": USER_ID,
        "ARXEN_SYNTHETIC_TOKEN": TOKEN,
    }


@pytest.mark.parametrize("environment", [{}, {"ARXEN_ENV": "development"}])
def test_identity_is_disabled_by_default(environment) -> None:
    assert load_synthetic_identity(environment) is None


def test_disabled_mode_does_not_require_identity_or_token() -> None:
    assert load_synthetic_identity({"ARXEN_SYNTHETIC_AUTH_ENABLED": "false"}) is None


@pytest.mark.parametrize("environment", ["development", "test"])
def test_explicit_identity_is_stable_and_hides_token_in_repr(environment) -> None:
    settings = enabled_environment() | {"ARXEN_ENV": environment}

    identity = load_synthetic_identity(settings)

    assert identity is not None
    assert identity.user_id == UUID(USER_ID)
    assert identity.token == TOKEN
    assert load_synthetic_identity(settings) == identity
    assert TOKEN not in repr(identity)


@pytest.mark.parametrize("environment", ["", "production", "staging", "tesst"])
def test_enabled_identity_is_rejected_outside_development_and_test(environment) -> None:
    with pytest.raises(ConfigurationError, match="development or test"):
        load_synthetic_identity(enabled_environment() | {"ARXEN_ENV": environment})


@pytest.mark.parametrize("value", ["yes", "1", "", "tru"])
def test_invalid_opt_in_value_is_rejected(value) -> None:
    with pytest.raises(ConfigurationError, match="ARXEN_SYNTHETIC_AUTH_ENABLED"):
        load_synthetic_identity(
            enabled_environment() | {"ARXEN_SYNTHETIC_AUTH_ENABLED": value}
        )


@pytest.mark.parametrize(
    "value", ["", "not-a-uuid", "00000000-0000-0000-0000-000000000000"]
)
def test_missing_or_invalid_user_identity_is_rejected(value) -> None:
    with pytest.raises(ConfigurationError, match="ARXEN_SYNTHETIC_USER_ID"):
        load_synthetic_identity(
            enabled_environment() | {"ARXEN_SYNTHETIC_USER_ID": value}
        )


@pytest.mark.parametrize("value", ["", "   ", "has a space", "has\na-newline"])
def test_empty_or_whitespace_token_is_rejected_without_echo(value) -> None:
    with pytest.raises(ConfigurationError, match="ARXEN_SYNTHETIC_TOKEN") as error:
        load_synthetic_identity(
            enabled_environment() | {"ARXEN_SYNTHETIC_TOKEN": value}
        )
    if value.strip():
        assert value not in str(error.value)
