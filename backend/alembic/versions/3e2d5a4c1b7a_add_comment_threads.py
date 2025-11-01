"""add comment thread models

Revision ID: 3e2d5a4c1b7a
Revises: 52235a18439d
Create Date: 2025-11-01 19:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3e2d5a4c1b7a"
down_revision: Union[str, Sequence[str], None] = "52235a18439d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "comment_threads",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("created_by_id", sa.UUID(), nullable=True),
        sa.Column("view_id", sa.String(), nullable=False),
        sa.Column("pin_x", sa.Float(), nullable=False),
        sa.Column("pin_y", sa.Float(), nullable=False),
        sa.Column("annotation", sa.JSON(), nullable=True),
        sa.Column("is_resolved", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("resolved_by_id", sa.UUID(), nullable=True),
        sa.Column("resolved_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["resolved_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_comment_threads_project", "comment_threads", ["project_id"], unique=False)
    op.create_index(
        "idx_comment_threads_view",
        "comment_threads",
        ["project_id", "view_id"],
        unique=False,
    )

    op.create_table(
        "thread_comments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("thread_id", sa.UUID(), nullable=False),
        sa.Column("author_id", sa.UUID(), nullable=True),
        sa.Column("parent_id", sa.UUID(), nullable=True),
        sa.Column("guest_name", sa.String(length=255), nullable=True),
        sa.Column("guest_email", sa.String(length=255), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["thread_id"], ["comment_threads.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["parent_id"], ["thread_comments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_thread_comments_thread", "thread_comments", ["thread_id"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_thread_comments_thread", table_name="thread_comments")
    op.drop_table("thread_comments")
    op.drop_index("idx_comment_threads_view", table_name="comment_threads")
    op.drop_index("idx_comment_threads_project", table_name="comment_threads")
    op.drop_table("comment_threads")
