"""from tasks.status into tasks.is_done

Revision ID: 44a756f00e9a
Revises: 4c1988743d55
Create Date: 2023-06-28 18:28:41.581983

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '44a756f00e9a'
down_revision = '4c1988743d55'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('tasks', sa.Column('is_done', sa.Boolean(), nullable=True))
    op.drop_column('tasks', 'status')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('tasks', sa.Column('status', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.drop_column('tasks', 'is_done')
    # ### end Alembic commands ###