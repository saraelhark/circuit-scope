"""add project processing status

Revision ID: 4f1e2d3c4b5a
Revises: 3e2d5a4c1b7a
Create Date: 2025-11-22 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4f1e2d3c4b5a"
down_revision: Union[str, Sequence[str], None] = "3e2d5a4c1b7a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "projects",
        sa.Column(
            "processing_status", sa.String(), nullable=False, server_default="completed"
        ),
    )
    op.add_column("projects", sa.Column("processing_error", sa.Text(), nullable=True))
    # Remove server default after creation so future inserts are strict if needed,
    # though keeping it doesn't hurt for existing rows.
    # Ideally we want 'queued' for new ones but 'completed' for existing.
    op.alter_column("projects", "processing_status", server_default="queued")


def downgrade() -> None:
    op.drop_column("projects", "processing_error")
    op.drop_column("projects", "processing_status")
