"""add view count

Revision ID: 5g2f3d4e5c6b
Revises: 4f1e2d3c4b5a
Create Date: 2025-11-23 12:00:00.000000

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "5g2f3d4e5c6b"
down_revision: Union[str, Sequence[str], None] = "4f1e2d3c4b5a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "projects",
        sa.Column("view_count", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("projects", "view_count")
