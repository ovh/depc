"""Add metas' column to 'teams' table

Revision ID: 956e9a3dd287
Revises: 30126831f6eb
Create Date: 2019-06-10 15:26:59.707588

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '956e9a3dd287'
down_revision = '30126831f6eb'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('teams', sa.Column('metas', sa.LargeBinary(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('teams', 'metas')
    # ### end Alembic commands ###