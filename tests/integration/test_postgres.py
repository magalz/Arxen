"""Synthetic PostgreSQL/pgvector smoke tests, without application domain tables."""

import psycopg
import pytest

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    "payload",
    [
        "arxen smoke",
        "Texto sintético: ação e memória",
        "O'Reilly",
        "'); DROP TABLE arxen_smoke_text; --",
    ],
    ids=["plain", "unicode", "quote", "sql-shaped-text"],
)
def test_parameterized_text_roundtrip(
    connection: psycopg.Connection[tuple[object, ...]], payload: str
) -> None:
    connection.execute(
        "CREATE TEMP TABLE arxen_smoke_text (payload text NOT NULL) ON COMMIT DROP"
    )
    connection.execute("INSERT INTO arxen_smoke_text (payload) VALUES (%s)", (payload,))

    result = connection.execute("SELECT payload FROM arxen_smoke_text").fetchall()

    assert result == [(payload,)]


def test_vector_roundtrip_and_euclidean_distance(
    connection: psycopg.Connection[tuple[object, ...]],
) -> None:
    connection.execute(
        "CREATE TEMP TABLE arxen_smoke_vectors "
        "(id integer PRIMARY KEY, embedding vector(3) NOT NULL) ON COMMIT DROP"
    )
    connection.execute(
        "INSERT INTO arxen_smoke_vectors (id, embedding) "
        "VALUES (%s, %s::vector), (%s, %s::vector)",
        (1, "[1,2,3]", 2, "[4,6,3]"),
    )

    stored = connection.execute(
        "SELECT embedding::text FROM arxen_smoke_vectors WHERE id = %s", (1,)
    ).fetchone()
    ranked = connection.execute(
        "SELECT id, embedding <-> %s::vector AS distance "
        "FROM arxen_smoke_vectors ORDER BY distance, id",
        ("[1,2,3]",),
    ).fetchall()

    assert stored == ("[1,2,3]",)
    assert [row[0] for row in ranked] == [1, 2]
    assert [row[1] for row in ranked] == pytest.approx([0.0, 5.0])


def test_rollback_removes_temporary_table(
    connection: psycopg.Connection[tuple[object, ...]],
) -> None:
    with connection.transaction(force_rollback=True):
        connection.execute(
            "CREATE TEMP TABLE arxen_smoke_rollback "
            "(payload text NOT NULL) ON COMMIT DROP"
        )
        connection.execute(
            "INSERT INTO arxen_smoke_rollback (payload) VALUES (%s)", ("synthetic",)
        )
        assert connection.execute(
            "SELECT payload FROM arxen_smoke_rollback"
        ).fetchone() == ("synthetic",)

    assert connection.execute(
        "SELECT to_regclass('pg_temp.arxen_smoke_rollback')"
    ).fetchone() == (None,)
