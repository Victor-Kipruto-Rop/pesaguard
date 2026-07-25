"""Add signing_secret to webhook_configs.

Required by the webhook_manager.py fix: signatures previously used
webhook_id itself as the HMAC key, but webhook_id is returned to the
customer in plaintext at registration — not a secret — so anyone who knew
a webhook's ID could forge a validly-signed payload. This adds a real,
separately-generated, non-guessable secret per webhook.

Nullable so existing rows (registered before this column existed) don't
break; webhook_manager.py logs loudly rather than silently signing
insecurely when this is NULL, until the row is backfilled or the webhook
is re-registered.

Revision ID: 20260725_add_webhook_signing_secret
Revises: 20260722_add_transaction_constraints
Create Date: 2026-07-25 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260725_add_webhook_signing_secret'
down_revision = '20260722_add_transaction_constraints'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'webhook_configs',
        sa.Column('signing_secret', sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('webhook_configs', 'signing_secret')
