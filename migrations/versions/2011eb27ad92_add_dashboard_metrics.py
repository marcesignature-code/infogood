"""add dashboard metrics

Revision ID: 2011eb27ad92
Revises:
Create Date: 2026-04-22 17:07:15.350540
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '2011eb27ad92'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'dashboard_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('active_listings_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_views', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_saved', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_reviews', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('wallet_balance_usd', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0'),
        sa.Column('wallet_total_earning_usd', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0'),
        sa.Column('wallet_total_orders', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dashboard_metrics_user_id'), 'dashboard_metrics', ['user_id'], unique=True)


def downgrade():
    op.drop_index(op.f('ix_dashboard_metrics_user_id'), table_name='dashboard_metrics')
    op.drop_table('dashboard_metrics')