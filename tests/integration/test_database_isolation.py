"""Test fixtures must not migrate or downgrade a different database by URL override."""

from urllib.parse import urlsplit

import psycopg
import pytest


@pytest.mark.parametrize(
    "suffix",
    [
        "?dbname=arxen_test",
        "?%64bname=arxen_test",
        "?dbname=postgresql%3A%2F%2Fexample.invalid%2Farxen_test",
        "?service=synthetic",
        "?host=example.invalid",
        "?sslmode=require",
        "#dbname=arxen_test",
    ],
)
def test_ambiguous_url_is_rejected_before_any_database_io(
    temporary_database_factory, monkeypatch, suffix
) -> None:
    def forbid_connection(*args, **kwargs):
        pytest.fail("Database I/O attempted before rejecting the ambiguous URL")

    monkeypatch.setattr(psycopg, "connect", forbid_connection)

    with pytest.raises(ValueError, match="query parameters or fragments"):
        with temporary_database_factory(
            f"postgresql://example.invalid/arxen_test{suffix}"
        ):
            pytest.fail("Ambiguous test database URL was accepted")


def test_dbname_override_is_rejected_and_preserves_owned_base_database(
    empty_database_url, temporary_database_factory
) -> None:
    base_name = urlsplit(empty_database_url).path.removeprefix("/")
    with psycopg.connect(empty_database_url) as connection:
        connection.execute("CREATE TABLE synthetic_sentinel (value text NOT NULL)")
        connection.execute("INSERT INTO synthetic_sentinel VALUES ('preserved')")

    # This parent is itself disposable; never exercise downgrade on a routed URL.
    with pytest.raises(ValueError, match="query parameters or fragments"):
        with temporary_database_factory(f"{empty_database_url}?dbname={base_name}"):
            pytest.fail("An override of the temporary database name was accepted")

    with psycopg.connect(empty_database_url) as connection:
        assert connection.execute(
            "SELECT value FROM synthetic_sentinel"
        ).fetchall() == [("preserved",)]


def test_destination_is_verified_before_yield_and_mismatch_cleans_up(
    empty_database_url, temporary_database_factory, monkeypatch
) -> None:
    real_connect = psycopg.connect
    attempted_targets = []

    def misroute_probe(conninfo, **kwargs):
        if conninfo != empty_database_url:
            attempted_targets.append(urlsplit(conninfo).path.removeprefix("/"))
            return real_connect(empty_database_url, **kwargs)
        return real_connect(conninfo, **kwargs)

    monkeypatch.setattr(psycopg, "connect", misroute_probe)

    with pytest.raises(RuntimeError, match="destination"):
        with temporary_database_factory(empty_database_url):
            pytest.fail("An unverified database destination was accepted")

    assert len(attempted_targets) == 1
    with real_connect(empty_database_url) as connection:
        assert (
            connection.execute(
                "SELECT datname FROM pg_database WHERE datname = %s",
                (attempted_targets[0],),
            ).fetchone()
            is None
        )
