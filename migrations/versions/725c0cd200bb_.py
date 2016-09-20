"""Initial revision.

Revision ID: 725c0cd200bb
Revises: None
Create Date: 2016-09-20 07:26:49.539574

"""

# revision identifiers, used by Alembic.
revision = '725c0cd200bb'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    """Build the initial version of the 'things' table."""
    op.create_table(
        'things',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String, nullable=False,
                  server_default='NONAME'),
        sa.Column('date_created', sa.DateTime, nullable=False,
                  server_default='1970-01-01T00:00:00Z'),
        sa.Column('date_modified', sa.DateTime(), nullable=False,
                  server_default='1970-01-01T00:00:00Z'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    """Nowhere to go from here."""
    op.drop_table('things')
