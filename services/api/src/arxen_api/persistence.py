"""Internal PostgreSQL access. Callers own authorization and transaction boundaries.

No method commits or opens a public access path. Case IDs are scope selectors,
not credentials. Domain routes must establish authorization before using this API.
"""

from uuid import UUID

import psycopg

from arxen_api.contracts import Case


class CoreRepository:
    def __init__(self, connection: psycopg.Connection[tuple[object, ...]]) -> None:
        self.connection = connection

    def create_case(self, title: str = "Novo caso") -> Case:
        raise NotImplementedError("Case creation is not implemented")

    def get_case(self, case_id: UUID) -> Case | None:
        raise NotImplementedError("Case reading is not implemented")
