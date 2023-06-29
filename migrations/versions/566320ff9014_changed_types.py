"""changed types

Revision ID: 566320ff9014
Revises: 44a756f00e9a
Create Date: 2023-06-28 18:51:18.936293

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '566320ff9014'
down_revision = '44a756f00e9a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('tasks', sa.Column('description', sa.String(), nullable=True))
    op.add_column('tasks', sa.Column('assigned_to_id', sa.Integer(), nullable=True))
    op.drop_constraint('tasks_staff_id_fkey', 'tasks', type_='foreignkey')
    op.create_foreign_key(None, 'tasks', 'users', ['assigned_to_id'], ['id'])
    op.drop_column('tasks', 'staff_id')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('tasks', sa.Column('staff_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'tasks', type_='foreignkey')
    op.create_foreign_key('tasks_staff_id_fkey', 'tasks', 'users', ['staff_id'], ['id'])
    op.drop_column('tasks', 'assigned_to_id')
    op.drop_column('tasks', 'description')
    # ### end Alembic commands ###