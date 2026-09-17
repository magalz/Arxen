"""Persist synthetic message submission keys and authorship.

Revision ID: 20260916_0004
Revises: 20260916_0003
"""

from alembic import op

revision: str = "20260916_0004"
down_revision: str = "20260916_0003"
branch_labels: None = None
depends_on: None = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE synthetic_case_owners "
        "ADD CONSTRAINT synthetic_case_owners_identity_key "
        "UNIQUE (case_id, owner_user_id)"
    )
    op.execute(
        """
        CREATE TABLE synthetic_message_submissions (
            case_id uuid NOT NULL,
            owner_user_id uuid NOT NULL,
            client_message_id uuid NOT NULL CHECK (
                client_message_id <> '00000000-0000-0000-0000-000000000000'::uuid
            ),
            message_id uuid NOT NULL,
            PRIMARY KEY (case_id, owner_user_id, client_message_id),
            UNIQUE (case_id, message_id),
            FOREIGN KEY (case_id, owner_user_id)
                REFERENCES synthetic_case_owners(case_id, owner_user_id),
            FOREIGN KEY (case_id, message_id) REFERENCES messages(case_id, id)
        )
        """
    )
    op.execute(
        "CREATE TRIGGER submissions_preserve_history "
        "BEFORE UPDATE OR DELETE ON synthetic_message_submissions "
        "FOR EACH ROW EXECUTE FUNCTION prevent_history_mutation()"
    )


def downgrade() -> None:
    op.execute("DROP TABLE synthetic_message_submissions")
    op.execute(
        "ALTER TABLE synthetic_case_owners "
        "DROP CONSTRAINT synthetic_case_owners_identity_key"
    )
