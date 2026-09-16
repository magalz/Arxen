"""Operational instants must be unambiguous and returned in UTC."""

from datetime import UTC, datetime, timedelta, timezone
from uuid import uuid4

import pytest

from arxen_api.contracts import StoredRecord


@pytest.mark.parametrize("offset", [-3, 0, 5.5])
def test_stored_instant_is_normalized_without_changing_the_instant(
    offset: float,
) -> None:
    instant = datetime(2026, 1, 2, 12, 30, tzinfo=timezone(timedelta(hours=offset)))

    record = StoredRecord(id=uuid4(), created_at=instant)

    assert record.created_at.tzinfo is UTC
    assert record.created_at == instant


def test_ambiguous_naive_instant_is_rejected() -> None:
    with pytest.raises(ValueError, match="timezone"):
        StoredRecord(id=uuid4(), created_at=datetime(2026, 1, 2, 12, 30))
