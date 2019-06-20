"""Remove Logs table

Revision ID: d2dc7ff020a0
Revises: 48570234e11c
Create Date: 2019-06-20 14:30:42.924837

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy_utils import UUIDType


# revision identifiers, used by Alembic.
revision = 'd2dc7ff020a0'
down_revision = '48570234e11c'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_index(op.f('ix_logs_created_at'), table_name='logs')
    op.drop_table('logs')


def downgrade():
    op.create_table(
        'logs',
        sa.Column('id', UUIDType(binary=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('level', sa.String(length=10), nullable=False),
        sa.Column('message', sa.String(), nullable=False),
        sa.Column('key', sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_logs_created_at'), 'logs', ['created_at'], unique=False)
