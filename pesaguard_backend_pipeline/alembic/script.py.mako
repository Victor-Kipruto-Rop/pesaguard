'''"""A generic script template for Alembic migrations."""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '${REVISION}'
down_revision = ${DOWN_REVISION}
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
