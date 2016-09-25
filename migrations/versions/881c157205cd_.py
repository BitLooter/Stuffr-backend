"""Added 'deleted' field.

Revision ID: 881c157205cd
Revises: 705d5507fc92
Create Date: 2016-09-24 23:32:19.975987

"""

# revision identifiers, used by Alembic.
revision = '881c157205cd'
down_revision = '705d5507fc92'

from alembic import op
import sqlalchemy as sa


def upgrade():
    """Add 'date_deleted' field indicating when a Thing was deleted.

    NULL means not deleted. At some point non-NULL rows may be purged after
    a certain age.
    """
    op.add_column('things', sa.Column('date_deleted', sa.DateTime(),
                                      nullable=True))


def downgrade():
    """Remove 'data_deleted' column."""
    with op.batch_alter_table('things', schema=None) as batch_op:
        batch_op.drop_column('date_deleted')
