"""Add unique constraint and indices for webhook idempotency and performance.

Revision ID: 20260722_add_transaction_constraints
Revises: 20260719_add_deadletters_reports_audit
Create Date: 2026-07-22 07:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260722_add_transaction_constraints'
down_revision = '20260719_add_deadletters_reports_audit'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add unique constraint to transactions.trans_id (idempotency key)
    op.create_unique_constraint(
        'uq_transaction_trans_id',
        'transactions',
        ['trans_id']
    )
    
    # Add indices for query performance
    op.create_index(
        'ix_transaction_trans_id',
        'transactions',
        ['trans_id'],
        unique=False
    )
    op.create_index(
        'ix_transaction_created_at',
        'transactions',
        ['created_at'],
        unique=False
    )
    
    # Add indices to discrepancies table for filtering and joins
    op.create_index(
        'ix_discrepancy_trans_id',
        'discrepancies',
        ['trans_id'],
        unique=False
    )
    op.create_index(
        'ix_discrepancy_tenant_id',
        'discrepancies',
        ['tenant_id'],
        unique=False
    )
    op.create_index(
        'ix_discrepancy_detected_at',
        'discrepancies',
        ['detected_at'],
        unique=False
    )


def downgrade() -> None:
    # Remove indices and constraint
    op.drop_index('ix_discrepancy_detected_at', table_name='discrepancies')
    op.drop_index('ix_discrepancy_tenant_id', table_name='discrepancies')
    op.drop_index('ix_discrepancy_trans_id', table_name='discrepancies')
    op.drop_index('ix_transaction_created_at', table_name='transactions')
    op.drop_index('ix_transaction_trans_id', table_name='transactions')
    op.drop_constraint('uq_transaction_trans_id', 'transactions', type_='unique')
