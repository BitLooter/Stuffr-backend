"""Initial revision.

Revision ID: 506fbee69570
Revises:
Create Date: 2016-09-13 03:44:33.815057

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '506fbee69570'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():  # NOQA
    op.create_table(
        'things',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String, nullable=False,
                  server_default='NONAME'),
        sa.Column('date_created', sa.DateTime, nullable=False,
                  server_default='1970-01-01T00:00:00Z'),
        sa.Column('date_updated', sa.DateTime(), nullable=False,
                  server_default='1970-01-01T00:00:00Z')
    )


def downgrade():  # NOQA
    pass
