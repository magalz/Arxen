"""Bind synthetic development cases to their configured identity.

Revision ID: 20260916_0003
Revises: 20260916_0002
"""

from alembic import op

revision: str = "20260916_0003"
down_revision: str = "20260916_0002"
branch_labels: None = None
depends_on: None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE synthetic_case_owners (
            case_id uuid PRIMARY KEY REFERENCES cases(id),
            owner_user_id uuid NOT NULL CHECK (
                owner_user_id <> '00000000-0000-0000-0000-000000000000'::uuid
            )
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE synthetic_case_owners")
