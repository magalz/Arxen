"""Internal PostgreSQL access. Callers own authorization and transaction boundaries.

No method commits or opens a public access path. Case IDs are scope selectors,
not credentials. Domain routes must establish authorization before using this API.
"""

from uuid import UUID

import psycopg
from psycopg.rows import class_row

from arxen_api.contracts import Case, Message, MessageRole, Source


class CoreRepository:
    def __init__(self, connection: psycopg.Connection[tuple[object, ...]]) -> None:
        self.connection = connection

    def create_case(self, title: str = "Novo caso") -> Case:
        with self.connection.cursor(row_factory=class_row(Case)) as cursor:
            cursor.execute(
                "INSERT INTO cases (title) VALUES (%s) RETURNING id, title, created_at",
                (title,),
            )
            case = cursor.fetchone()
            assert case is not None
            return case

    def get_case(self, case_id: UUID) -> Case | None:
        with self.connection.cursor(row_factory=class_row(Case)) as cursor:
            cursor.execute(
                "SELECT id, title, created_at FROM cases WHERE id = %s", (case_id,)
            )
            return cursor.fetchone()

    def add_message(self, case_id: UUID, role: MessageRole, content: str) -> Message:
        with self.connection.cursor(row_factory=class_row(Message)) as cursor:
            cursor.execute(
                "INSERT INTO messages (case_id, role, content) VALUES (%s, %s, %s) "
                "RETURNING id, case_id, sequence, role, content, created_at",
                (case_id, role, content),
            )
            message = cursor.fetchone()
            assert message is not None
            return message

    def list_messages(self, case_id: UUID) -> list[Message]:
        with self.connection.cursor(row_factory=class_row(Message)) as cursor:
            cursor.execute(
                "SELECT id, case_id, sequence, role, content, created_at "
                "FROM messages WHERE case_id = %s ORDER BY sequence",
                (case_id,),
            )
            return cursor.fetchall()

    def create_message_source(
        self,
        case_id: UUID,
        message_id: UUID,
        start_offset: int,
        end_offset: int,
        excerpt: str,
    ) -> Source:
        raise NotImplementedError("Source persistence is not implemented")

    def get_source(self, case_id: UUID, source_id: UUID) -> Source | None:
        raise NotImplementedError("Source reading is not implemented")
