"""Added StuffrInfo model.

Revision ID: a1d047167424
Revises: 881c157205cd
Create Date: 2016-10-09 05:42:24.120916

"""

# revision identifiers, used by Alembic.
revision = 'a1d047167424'
down_revision = '881c157205cd'

from alembic import op
import sqlalchemy as sa


def upgrade():
    """Add the new StuffInfo model."""
    op.create_table(
        'stuffr_info',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('creator_name', sa.Unicode(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    """Remove the StuffrInfo model."""
    op.drop_table('stuffr_info')
