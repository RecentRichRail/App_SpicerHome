"""Add is_email_valid column to User model

Revision ID: 58ed93a90ccd
Revises: 
Create Date: 2024-11-27 22:33:50.634907

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '58ed93a90ccd'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('geo', sa.String(length=255), nullable=True))
        batch_op.alter_column('uid',
               existing_type=mysql.VARCHAR(length=40),
               nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('uid',
               existing_type=mysql.VARCHAR(length=40),
               nullable=True)
        batch_op.drop_column('geo')

    # ### end Alembic commands ###
