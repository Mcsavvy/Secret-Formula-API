"""changed chatmedia url type

Revision ID: e70d1c2e1441
Revises: a3855c5e53a6
Create Date: 2023-12-22 14:15:54.658206

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "e70d1c2e1441"
down_revision = "a3855c5e53a6"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("chat_media", schema=None) as batch_op:
        batch_op.alter_column(
            "url",
            existing_type=mysql.CHAR(
                collation="utf8mb3_unicode_ci", length=32
            ),
            type_=sa.String(length=255),
            existing_nullable=False,
        )
        batch_op.drop_index("url")

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("chat_media", schema=None) as batch_op:
        batch_op.create_index("url", ["url"], unique=True)
        batch_op.alter_column(
            "url",
            existing_type=sa.String(length=255),
            type_=mysql.CHAR(collation="utf8mb3_unicode_ci", length=32),
            existing_nullable=False,
        )

    # ### end Alembic commands ###
