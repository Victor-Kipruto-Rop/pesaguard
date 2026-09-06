"""Add persisted JWT revocation state.

Revision ID: 20260908_add_revoked_tokens
Revises: 20260907_add_refresh_token_records
Create Date: 2026-09-08 00:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260908_add_revoked_tokens"
down_revision = "20260907_add_refresh_token_records"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user_accounts",
        sa.Column("authorization_version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.create_table(
        "revoked_tokens",
        sa.Column("jti", sa.String(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("jti"),
    )


def downgrade() -> None:
    op.drop_table("revoked_tokens")
    op.drop_column("user_accounts", "authorization_version")
