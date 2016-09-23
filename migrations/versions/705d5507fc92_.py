"""Added description and notes columns.

Revision ID: 705d5507fc92
Revises: 725c0cd200bb
Create Date: 2016-09-23 07:01:16.325045

"""

# revision identifiers, used by Alembic.
revision = '705d5507fc92'
down_revision = '725c0cd200bb'

from alembic import op
import sqlalchemy as sa


def upgrade():
    """Two columns added."""
    op.add_column('things',
                  sa.Column('description', sa.UnicodeText(), nullable=True))
    op.add_column('things',
                  sa.Column('notes', sa.UnicodeText(), nullable=True))


def downgrade():
    """Remove two added columns."""
    op.drop_column('things', 'notes')
    op.drop_column('things', 'description')
