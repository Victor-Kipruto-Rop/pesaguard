"""Add settlement_attempts table

Revision ID: 20260906_add_settlement_attempts
Revises: 20260725_add_webhook_signing_secret
Create Date: 2026-09-06 00:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260906_add_settlement_attempts'
down_revision = '20260725_add_webhook_signing_secret'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'settlement_attempts',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('reference', sa.String(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('account_number', sa.String(), nullable=True),
        sa.Column('bank_name', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('response', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('attempt_number', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_attempt_at', sa.DateTime(timezone=True), nullable=True),
    )

    op.create_index('ix_settlement_tenant', 'settlement_attempts', ['tenant_id'])
    op.create_index('ix_settlement_reference', 'settlement_attempts', ['reference'])


def downgrade() -> None:
    op.drop_index('ix_settlement_reference', table_name='settlement_attempts')
    op.drop_index('ix_settlement_tenant', table_name='settlement_attempts')
    op.drop_table('settlement_attempts')
