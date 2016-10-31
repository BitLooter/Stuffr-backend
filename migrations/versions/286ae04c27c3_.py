"""Added several new columns, mostly in preperation for user authentication.

Note that 'name' has been split into first and last names, and the old one is
simply dropped. No databases with actual data exist yet so this isn't an issue.

Revision ID: 286ae04c27c3
Revises: 23bb7738f876
Create Date: 2016-10-31 00:36:22.660086
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '286ae04c27c3'
down_revision = '23bb7738f876'


def upgrade():
    """Add several new columns for users and tweak the database info table."""
    with op.batch_alter_table('stuffr_info', schema=None) as batch_op:
        batch_op.add_column(sa.Column('creator_version', sa.Unicode(),
                            nullable=False, server_default='UNKNOWN')),
        batch_op.add_column(sa.Column('date_created', sa.DateTime(),
                            nullable=False,
                            server_default='1970-01-01T00:00:00Z')),
        batch_op.add_column(sa.Column('database_version', sa.Integer(),
                            nullable=False, server_default='-1')),
    op.rename_table('stuffr_info', 'database_info')

    op.create_table(
        'role',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Unicode(), nullable=False),
        sa.Column('description', sa.Unicode(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('active', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('confirmed_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('current_login_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('current_login_ip', sa.Unicode(), nullable=True))
        batch_op.add_column(sa.Column('email', sa.Unicode(), nullable=False))
        batch_op.add_column(sa.Column('last_login_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('last_login_ip', sa.Unicode(), nullable=True))
        batch_op.add_column(sa.Column('login_count', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('name_first', sa.Unicode(), nullable=False))
        batch_op.add_column(sa.Column('name_last', sa.Unicode(), nullable=False))
        batch_op.add_column(sa.Column('password', sa.Unicode(), nullable=False))
        batch_op.drop_column('name')


def downgrade():
    """Remove new user columns and change back the database info table."""
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('name', sa.VARCHAR(), nullable=False))
        batch_op.drop_column('password')
        batch_op.drop_column('name_last')
        batch_op.drop_column('name_first')
        batch_op.drop_column('login_count')
        batch_op.drop_column('last_login_ip')
        batch_op.drop_column('last_login_at')
        batch_op.drop_column('email')
        batch_op.drop_column('current_login_ip')
        batch_op.drop_column('current_login_at')
        batch_op.drop_column('confirmed_at')
        batch_op.drop_column('active')

    with op.batch_alter_table('database_info', schema=None) as batch_op:
        batch_op.drop_column('creator_version')
        batch_op.drop_column('date_created')
        batch_op.drop_column('database_version')
    op.rename_table('database_info', 'stuffr_info')

    op.drop_table('role')
