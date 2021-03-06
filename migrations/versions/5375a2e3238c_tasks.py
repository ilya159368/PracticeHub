"""tasks

Revision ID: 5375a2e3238c
Revises: 7c109e020a2a
Create Date: 2022-04-16 19:12:39.567108

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5375a2e3238c'
down_revision = '7c109e020a2a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('page', schema=None) as batch_op:
        batch_op.add_column(sa.Column('add_task', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('page', schema=None) as batch_op:
        batch_op.drop_column('add_task')

    # ### end Alembic commands ###
