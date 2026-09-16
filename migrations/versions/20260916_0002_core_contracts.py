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
            created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE cases")
