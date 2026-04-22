"""add bookmarks table

Revision ID: 6d5f7a2c1b3e
Revises: 2011eb27ad92
Create Date: 2026-04-22 21:05:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "6d5f7a2c1b3e"
down_revision = "2011eb27ad92"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "bookmarks",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("listing_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "listing_id"),
    )
    op.create_index(
        op.f("ix_bookmarks_user_id"), "bookmarks", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_bookmarks_listing_id"), "bookmarks", ["listing_id"], unique=False
    )
    op.create_index(
        op.f("ix_bookmarks_created_at"), "bookmarks", ["created_at"], unique=False
    )


def downgrade():
    op.drop_index(op.f("ix_bookmarks_created_at"), table_name="bookmarks")
    op.drop_index(op.f("ix_bookmarks_listing_id"), table_name="bookmarks")
    op.drop_index(op.f("ix_bookmarks_user_id"), table_name="bookmarks")
    op.drop_table("bookmarks")
