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


def downgrade() -> None:
    op.execute("DROP TABLE messages")
    op.execute("DROP FUNCTION assign_message_sequence()")
    op.execute("DROP FUNCTION prevent_history_mutation()")
    op.execute("DROP TABLE cases")
