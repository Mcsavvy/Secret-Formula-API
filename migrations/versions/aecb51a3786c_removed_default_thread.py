"""removed_default_thread

Revision ID: aecb51a3786c
Revises: 547068f5ddda
Create Date: 2023-11-13 22:12:04.500489

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "aecb51a3786c"
down_revision = "547068f5ddda"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("thread", schema=None) as batch_op:
        batch_op.drop_column("default")

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("thread", schema=None) as batch_op:
        batch_op.add_column(sa.Column("default", sa.Boolean(), nullable=False))

    # ### end Alembic commands ###