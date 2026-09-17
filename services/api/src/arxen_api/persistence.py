"""Internal PostgreSQL access. Callers own authorization and transaction boundaries.

No method commits or opens a public access path. Case IDs are scope selectors,
not credentials. Domain routes must establish authorization before using this API.
"""

from uuid import UUID

import psycopg
from psycopg.pq import TransactionStatus
from psycopg.rows import class_row
from psycopg.types.json import Jsonb

from arxen_api.contracts import Case, Event, Message, MessageRole, Source, Task
from arxen_api.conversation import MessageConflict


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

    def create_owned_case(self, owner_user_id: UUID, title: str = "Novo caso") -> Case:
        """Insert the case and binding atomically; the caller still owns commit."""
        with self.connection.cursor(row_factory=class_row(Case)) as cursor:
            cursor.execute(
                "WITH new_case AS ("
                "INSERT INTO cases (title) VALUES (%s) RETURNING id, title, created_at"
                "), binding AS ("
                "INSERT INTO synthetic_case_owners (case_id, owner_user_id) "
                "SELECT id, %s FROM new_case RETURNING case_id"
                ") SELECT c.id, c.title, c.created_at FROM new_case c "
                "JOIN binding b ON b.case_id = c.id",
                (title, owner_user_id),
            )
            case = cursor.fetchone()
            assert case is not None
            return case

    def get_owned_case(self, owner_user_id: UUID, case_id: UUID) -> Case | None:
        """Scope every synthetic read to the identity validated by the server."""
        with self.connection.cursor(row_factory=class_row(Case)) as cursor:
            cursor.execute(
                "SELECT c.id, c.title, c.created_at FROM cases c "
                "JOIN synthetic_case_owners o ON o.case_id = c.id "
                "WHERE c.id = %s AND o.owner_user_id = %s",
                (case_id, owner_user_id),
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

    def submit_owned_message(
        self, owner_user_id: UUID, case_id: UUID, client_message_id: UUID, content: str
    ) -> tuple[Message, bool] | None:
        """Serialize a submission within the caller's transaction and identity."""
        if (
            self.connection.autocommit
            and self.connection.info.transaction_status == TransactionStatus.IDLE
        ):
            raise ValueError("Message submission requires a caller-owned transaction")
        authorized = self.connection.execute(
            "SELECT c.id FROM cases c "
            "JOIN synthetic_case_owners o ON o.case_id=c.id "
            "WHERE c.id=%s AND o.owner_user_id=%s FOR UPDATE OF c, o",
            (case_id, owner_user_id),
        ).fetchone()
        if authorized is None:
            return None

        # The case lock also orders the existing message-sequence trigger. A
        # retried concurrent request observes the predecessor after its commit.
        with self.connection.cursor(row_factory=class_row(Message)) as cursor:
            cursor.execute(
                "SELECT m.id, m.case_id, m.sequence, m.role, m.content, m.created_at "
                "FROM messages m JOIN synthetic_message_submissions s "
                "ON s.case_id=m.case_id AND s.message_id=m.id "
                "WHERE s.case_id=%s AND s.owner_user_id=%s AND s.client_message_id=%s",
                (case_id, owner_user_id, client_message_id),
            )
            previous = cursor.fetchone()
        if previous is not None:
            if previous.content != content:
                raise MessageConflict("Message submission conflict")
            return previous, False

        message = self.add_message(case_id, "user", content)
        self.connection.execute(
            "INSERT INTO synthetic_message_submissions "
            "(case_id, owner_user_id, client_message_id, message_id) "
            "VALUES (%s,%s,%s,%s)",
            (case_id, owner_user_id, client_message_id, message.id),
        )
        return message, True

    def list_owned_messages(
        self, owner_user_id: UUID, case_id: UUID, *, after_sequence: int, limit: int
    ) -> list[Message] | None:
        """Read a bounded page, retaining identity scope in the message query."""
        if self.get_owned_case(owner_user_id, case_id) is None:
            return None
        with self.connection.cursor(row_factory=class_row(Message)) as cursor:
            cursor.execute(
                "SELECT m.id, m.case_id, m.sequence, m.role, m.content, m.created_at "
                "FROM messages m JOIN synthetic_case_owners o ON o.case_id=m.case_id "
                "WHERE m.case_id=%s AND o.owner_user_id=%s AND m.sequence>%s "
                "ORDER BY m.sequence LIMIT %s",
                (case_id, owner_user_id, after_sequence, limit),
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
