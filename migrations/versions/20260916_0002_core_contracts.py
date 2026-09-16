"""Persist the central foundation contracts.

Revision ID: 20260916_0002
Revises: 20260916_0001
"""

from alembic import op

revision: str = "20260916_0002"
down_revision: str = "20260916_0001"
branch_labels: None = None
depends_on: None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE cases (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            title text NOT NULL CHECK (btrim(title) <> ''),
            message_sequence bigint NOT NULL DEFAULT 0 CHECK (message_sequence >= 0),
            event_sequence bigint NOT NULL DEFAULT 0 CHECK (event_sequence >= 0),
            created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    op.execute(
        """
        CREATE TABLE messages (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            case_id uuid NOT NULL REFERENCES cases(id),
            sequence bigint NOT NULL CHECK (sequence > 0),
            role text NOT NULL CHECK (role IN ('user', 'assistant')),
            content text NOT NULL CHECK (btrim(content) <> ''),
            created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (case_id, id),
            UNIQUE (case_id, sequence)
        )
        """
    )
    op.execute(
        """
        CREATE FUNCTION assign_message_sequence() RETURNS trigger
        LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
        BEGIN
            IF NEW.sequence IS NOT NULL THEN
                RAISE EXCEPTION 'Message sequence is assigned by the server'
                    USING ERRCODE = '23514';
            END IF;
            UPDATE cases SET message_sequence = message_sequence + 1
                WHERE id = NEW.case_id RETURNING message_sequence INTO NEW.sequence;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'Message requires an existing case'
                    USING ERRCODE = '23503';
            END IF;
            RETURN NEW;
        END;
        $$
        """
    )
    op.execute(
        "CREATE TRIGGER messages_sequence BEFORE INSERT ON messages "
        "FOR EACH ROW EXECUTE FUNCTION assign_message_sequence()"
    )
    op.execute(
        """
        CREATE FUNCTION prevent_history_mutation() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'Historical rows are append-only'
                USING ERRCODE = '23514';
        END;
        $$
        """
    )
    op.execute(
        "CREATE TRIGGER messages_preserve_history BEFORE UPDATE OR DELETE ON messages "
        "FOR EACH ROW EXECUTE FUNCTION prevent_history_mutation()"
    )
    op.execute(
        """
        CREATE TABLE sources (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            case_id uuid NOT NULL REFERENCES cases(id),
            kind text NOT NULL DEFAULT 'message' CHECK (kind = 'message'),
            message_id uuid NOT NULL,
            start_offset integer NOT NULL CHECK (start_offset >= 0),
            end_offset integer NOT NULL CHECK (end_offset > start_offset),
            excerpt text NOT NULL,
            created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT sources_message_case_fk FOREIGN KEY (case_id, message_id)
                REFERENCES messages(case_id, id)
        )
        """
    )
    op.execute("CREATE INDEX sources_message_idx ON sources(case_id, message_id)")
    op.execute(
        """
        CREATE FUNCTION validate_message_source() RETURNS trigger
        LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
        DECLARE
            message_text text;
        BEGIN
            SELECT content INTO message_text FROM messages
                WHERE case_id = NEW.case_id AND id = NEW.message_id;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'Source requires a message from the same case'
                    USING ERRCODE = '23503';
            END IF;
            IF NEW.start_offset IS NULL OR NEW.end_offset IS NULL
                OR NEW.start_offset < 0 OR NEW.end_offset <= NEW.start_offset
                OR NEW.end_offset > char_length(message_text) THEN
                RAISE EXCEPTION 'Source offsets are outside the message'
                    USING ERRCODE = '23514';
            END IF;
            IF NEW.excerpt IS DISTINCT FROM substring(
                message_text FROM NEW.start_offset + 1
                FOR NEW.end_offset - NEW.start_offset
            ) THEN
                RAISE EXCEPTION 'Source excerpt does not match the message'
                    USING ERRCODE = '23514';
            END IF;
            RETURN NEW;
        END;
        $$
        """
    )
    op.execute(
        "CREATE TRIGGER sources_locator BEFORE INSERT ON sources "
        "FOR EACH ROW EXECUTE FUNCTION validate_message_source()"
    )
    op.execute(
        "CREATE TRIGGER sources_preserve_history BEFORE UPDATE OR DELETE ON sources "
        "FOR EACH ROW EXECUTE FUNCTION prevent_history_mutation()"
    )
    op.execute(
        """
        CREATE TABLE tasks (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            case_id uuid NOT NULL REFERENCES cases(id),
            objective text NOT NULL CHECK (btrim(objective) <> ''),
            state text NOT NULL DEFAULT 'draft' CHECK (state IN (
                'draft', 'queued', 'running', 'waiting_user', 'waiting_budget',
                'pause_requested', 'paused', 'recovering', 'completed',
                'failed', 'cancelled'
            )),
            created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (case_id, id)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE events (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            case_id uuid NOT NULL REFERENCES cases(id),
            sequence bigint NOT NULL CHECK (sequence > 0),
            event_type text NOT NULL CHECK (btrim(event_type) <> ''),
            actor text NOT NULL CHECK (btrim(actor) <> ''),
            task_id uuid,
            payload jsonb NOT NULL DEFAULT '{}'::jsonb
                CHECK (jsonb_typeof(payload) = 'object'),
            created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (case_id, sequence),
            CONSTRAINT events_task_case_fk FOREIGN KEY (case_id, task_id)
                REFERENCES tasks(case_id, id)
        )
        """
    )
    op.execute("CREATE INDEX events_task_idx ON events(case_id, task_id)")
    op.execute(
        """
        CREATE FUNCTION assign_event_sequence() RETURNS trigger
        LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
        BEGIN
            IF NEW.sequence IS NOT NULL THEN
                RAISE EXCEPTION 'Event sequence is assigned by the server'
                    USING ERRCODE = '23514';
            END IF;
            UPDATE cases SET event_sequence = event_sequence + 1
                WHERE id = NEW.case_id RETURNING event_sequence INTO NEW.sequence;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'Event requires an existing case'
                    USING ERRCODE = '23503';
            END IF;
            RETURN NEW;
        END;
        $$
        """
    )
    op.execute(
        "CREATE TRIGGER events_sequence BEFORE INSERT ON events "
        "FOR EACH ROW EXECUTE FUNCTION assign_event_sequence()"
    )
    op.execute(
        "CREATE TRIGGER events_preserve_history BEFORE UPDATE OR DELETE ON events "
        "FOR EACH ROW EXECUTE FUNCTION prevent_history_mutation()"
    )


def downgrade() -> None:
    op.execute("DROP TABLE events")
    op.execute("DROP FUNCTION assign_event_sequence()")
    op.execute("DROP TABLE tasks")
    op.execute("DROP TABLE sources")
    op.execute("DROP FUNCTION validate_message_source()")
    op.execute("DROP TABLE messages")
    op.execute("DROP FUNCTION assign_message_sequence()")
    op.execute("DROP FUNCTION prevent_history_mutation()")
    op.execute("DROP TABLE cases")
