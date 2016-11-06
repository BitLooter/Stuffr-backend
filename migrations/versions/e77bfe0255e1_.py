"""Add the rest of the information for Flask-Security.

Revision ID: e77bfe0255e1
Revises: 286ae04c27c3
Create Date: 2016-11-01 00:52:26.101604

"""

# revision identifiers, used by Alembic.
revision = 'e77bfe0255e1'
down_revision = '286ae04c27c3'

from alembic import op
import sqlalchemy as sa


def upgrade():
    """Add the many-to-many mapping for User/Role."""
    op.create_table(
        'roles_users',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['role.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], )
    )


def downgrade():
    """Remove User/Role mapping."""
    op.drop_table('roles_users')
