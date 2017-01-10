"""Initial database revision.

All previous revisions have been combined into this one. As no production
databases are in existance yet, this shouldn't cause any problems. It will also
make it much easier to make the changes needed to work under other database
engines.

Revision ID: b242e125adb8
Revises: None
Create Date: 2017-01-09 22:54:56.448201

"""

# revision identifiers, used by Alembic.
revision = 'b242e125adb8'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    """Initial database setup."""
    op.create_table(
        'database_info',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('creator_name', sa.Unicode(length=32), nullable=False),
        sa.Column('creator_version', sa.Unicode(length=32), nullable=False),
        sa.Column('date_created', sa.DateTime(), nullable=False),
        sa.Column('database_version', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'role',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Unicode(length=32), nullable=False),
        sa.Column('description', sa.Unicode(length=256)),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.Unicode(length=256), nullable=False),
        sa.Column('password', sa.Unicode(length=128), nullable=False),
        sa.Column('name_first', sa.Unicode(length=128), nullable=False),
        sa.Column('name_last', sa.Unicode(length=128), nullable=False),
        sa.Column('date_created', sa.DateTime(), nullable=False),
        sa.Column('active', sa.Boolean()),
        sa.Column('confirmed_at', sa.DateTime()),
        sa.Column('last_login_at', sa.DateTime()),
        sa.Column('current_login_at', sa.DateTime()),
        # Maximun length of an IPv6 address == 45
        sa.Column('last_login_ip', sa.Unicode(length=45)),
        sa.Column('current_login_ip', sa.Unicode(length=45)),
        sa.Column('login_count', sa.Integer()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'inventory',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Unicode(length=128), nullable=False),
        sa.Column('date_created', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'roles_users',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['role.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], )
    )
    op.create_table(
        'thing',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Unicode(length=128), nullable=False,
                  server_default='NONAME'),
        sa.Column('date_created', sa.DateTime(), nullable=False),
        sa.Column('date_modified', sa.DateTime(), nullable=False),
        sa.Column('date_deleted', sa.DateTime()),
        sa.Column('description', sa.UnicodeText()),
        sa.Column('notes', sa.UnicodeText()),
        sa.Column('inventory_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['inventory_id'], ['inventory.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    """BURN EVERYTHING."""
    op.drop_table('thing')
    op.drop_table('roles_users')
    op.drop_table('inventory')
    op.drop_table('user')
    op.drop_table('role')
    op.drop_table('database_info')
