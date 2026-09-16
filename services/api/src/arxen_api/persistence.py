"""Internal PostgreSQL access. Callers own authorization and transaction boundaries.

No method commits or opens a public access path. Case IDs are scope selectors,
not credentials. Domain routes must establish authorization before using this API.
"""

from uuid import UUID

import psycopg
from psycopg.rows import class_row
from psycopg.types.json import Jsonb

from arxen_api.contracts import Case, Event, Message, MessageRole, Source, Task


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
        with self.connection.cursor(row_factory=class_row(Source)) as cursor:
            cursor.execute(
                "INSERT INTO sources "
                "(case_id, message_id, start_offset, end_offset, excerpt) "
                "VALUES (%s, %s, %s, %s, %s) "
                "RETURNING id, case_id, kind, message_id, start_offset, end_offset, "
                "excerpt, created_at",
                (case_id, message_id, start_offset, end_offset, excerpt),
            )
            source = cursor.fetchone()
            assert source is not None
            return source

    def get_source(self, case_id: UUID, source_id: UUID) -> Source | None:
        with self.connection.cursor(row_factory=class_row(Source)) as cursor:
            cursor.execute(
                "SELECT id, case_id, kind, message_id, start_offset, end_offset, "
                "excerpt, created_at FROM sources WHERE case_id = %s AND id = %s",
                (case_id, source_id),
            )
            return cursor.fetchone()

    def create_task(self, case_id: UUID, objective: str) -> Task:
        with self.connection.cursor(row_factory=class_row(Task)) as cursor:
            cursor.execute(
                "INSERT INTO tasks (case_id, objective) VALUES (%s, %s) "
                "RETURNING id, case_id, objective, state, created_at",
                (case_id, objective),
            )
            task = cursor.fetchone()
            assert task is not None
            return task

    def get_task(self, case_id: UUID, task_id: UUID) -> Task | None:
        with self.connection.cursor(row_factory=class_row(Task)) as cursor:
            cursor.execute(
                "SELECT id, case_id, objective, state, created_at "
                "FROM tasks WHERE case_id = %s AND id = %s",
                (case_id, task_id),
            )
            return cursor.fetchone()

    def append_event(
        self,
        case_id: UUID,
        event_type: str,
        actor: str,
        *,
        task_id: UUID | None = None,
        payload: dict[str, object] | None = None,
    ) -> Event:
        with self.connection.cursor(row_factory=class_row(Event)) as cursor:
            cursor.execute(
                "INSERT INTO events (case_id, event_type, actor, task_id, payload) "
                "VALUES (%s, %s, %s, %s, %s) "
                "RETURNING id, case_id, sequence, event_type, actor, task_id, "
                "payload, created_at",
                (
                    case_id,
                    event_type,
                    actor,
                    task_id,
                    Jsonb({} if payload is None else payload),
                ),
            )
            event = cursor.fetchone()
            assert event is not None
            return event

    def list_events(self, case_id: UUID, *, after_sequence: int = 0) -> list[Event]:
        with self.connection.cursor(row_factory=class_row(Event)) as cursor:
            cursor.execute(
                "SELECT id, case_id, sequence, event_type, actor, task_id, "
                "payload, created_at FROM events "
                "WHERE case_id = %s AND sequence > %s ORDER BY sequence",
                (case_id, after_sequence),
            )
            return cursor.fetchall()
