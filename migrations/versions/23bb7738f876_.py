"""Rename Thing table and fix its 'name' type, and add User/Inventory tables.

Revision ID: 23bb7738f876
Revises: a1d047167424
Create Date: 2016-10-09 07:00:10.302237

"""

# revision identifiers, used by Alembic.
revision = '23bb7738f876'
down_revision = 'a1d047167424'

from alembic import op
import sqlalchemy as sa


def upgrade():
    """Rename a table, fix a string type, and add a couple new tables."""
    with op.batch_alter_table('things', schema=None) as batch_op:
        # 'name' column of Thing should be of type Unicode
        batch_op.alter_column(
            'name',
            existing_type=sa.VARCHAR(),
            type_=sa.Unicode(),
            existing_nullable=False,
            existing_server_default=sa.text("'NONAME'"))
        batch_op.add_column(sa.Column('inventory_id', sa.Integer(),
                                      nullable=False))
        batch_op.create_foreign_key('fk_thing_inventory', 'inventory',
                                    ['inventory_id'], ['id'])
    op.rename_table('things', 'thing')
    op.create_table(
        'inventory',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Unicode(), nullable=False),
        sa.Column('date_created', sa.DateTime(), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Unicode(), nullable=False),
        sa.Column('date_created', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    """Remove new tables and change thing name and type back."""
    op.rename_table('thing', 'things')
    with op.batch_alter_table('things', schema=None) as batch_op:
        batch_op.alter_column(
            'name',
            existing_type=sa.Unicode(),
            type_=sa.VARCHAR(),
            existing_nullable=False,
            existing_server_default=sa.text("'NONAME'"))
    op.drop_table('user')
    op.drop_table('inventory')
