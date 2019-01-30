"""Init database

Revision ID: 30126831f6eb
Revises: 
Create Date: 2019-01-14 12:00:56.901107

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils import UUIDType, JSONType

# revision identifiers, used by Alembic.
revision = '30126831f6eb'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
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
    op.create_table(
        'teams',
        sa.Column('id', UUIDType(binary=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_teams_created_at'), 'teams', ['created_at'], unique=False)
    op.create_table(
        'users',
        sa.Column('id', UUIDType(binary=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('admin', sa.Boolean(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_users_created_at'), 'users', ['created_at'], unique=False)
    op.create_table(
        'configs',
        sa.Column('id', UUIDType(binary=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('team_id', UUIDType(binary=False), nullable=False),
        sa.Column('data', JSONType(), nullable=False),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_configs_created_at'), 'configs', ['created_at'], unique=False)
    op.create_table(
        'grants',
        sa.Column('id', UUIDType(binary=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('user_id', UUIDType(binary=False), nullable=True),
        sa.Column('role', sa.Enum('member', 'editor', 'manager', name='rolenames'), nullable=False),
        sa.Column('team_id', UUIDType(binary=False), nullable=True),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_grants_created_at'), 'grants', ['created_at'], unique=False)
    op.create_table(
        'rules',
        sa.Column('id', UUIDType(binary=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('team_id', UUIDType(binary=False), nullable=True),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('team_id', 'name', name='team_rule_uc')
    )
    op.create_index(op.f('ix_rules_created_at'), 'rules', ['created_at'], unique=False)
    op.create_table(
        'sources',
        sa.Column('id', UUIDType(binary=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('plugin', sa.String(length=255), nullable=False),
        sa.Column('configuration', sa.LargeBinary(), nullable=True),
        sa.Column('team_id', UUIDType(binary=False), nullable=True),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sources_created_at'), 'sources', ['created_at'], unique=False)
    op.create_table(
        'worst',
        sa.Column('id', UUIDType(binary=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('team_id', UUIDType(binary=False), nullable=False),
        sa.Column('date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('label', sa.String(length=255), nullable=False),
        sa.Column('period', sa.Enum('daily', 'monthly', name='periods'), nullable=False),
        sa.Column('data', JSONType(), nullable=False),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('team_id', 'label', 'date', 'period', name='team_label_date_period_uc')
    )
    op.create_index(op.f('ix_worst_created_at'), 'worst', ['created_at'], unique=False)
    op.create_table(
        'checks',
        sa.Column('id', UUIDType(binary=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('source_id', UUIDType(binary=False), nullable=False),
        sa.Column('type', sa.String(length=255), nullable=False),
        sa.Column('parameters', JSONType(), nullable=True),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_checks_created_at'), 'checks', ['created_at'], unique=False)
    op.create_table(
        'rule_check_association',
        sa.Column('rule_id', UUIDType(binary=False), nullable=False),
        sa.Column('check_id', UUIDType(binary=False), nullable=False),
        sa.ForeignKeyConstraint(['check_id'], ['checks.id'], ),
        sa.ForeignKeyConstraint(['rule_id'], ['rules.id'], ),
        sa.PrimaryKeyConstraint('rule_id', 'check_id'),
        sa.UniqueConstraint('rule_id', 'check_id', name='rule_check_uix')
    )
    op.create_table(
        'variables',
        sa.Column('id', UUIDType(binary=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('value', sa.String(), nullable=False),
        sa.Column('type', sa.String(length=255), nullable=False),
        sa.Column('rule_id', UUIDType(binary=False), nullable=True),
        sa.Column('team_id', UUIDType(binary=False), nullable=False),
        sa.Column('source_id', UUIDType(binary=False), nullable=True),
        sa.Column('check_id', UUIDType(binary=False), nullable=True),
        sa.ForeignKeyConstraint(['check_id'], ['checks.id'], ),
        sa.ForeignKeyConstraint(['rule_id'], ['rules.id'], ),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_variables_created_at'), 'variables', ['created_at'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_variables_created_at'), table_name='variables')
    op.drop_table('variables')
    op.drop_table('rule_check_association')
    op.drop_index(op.f('ix_checks_created_at'), table_name='checks')
    op.drop_table('checks')
    op.drop_index(op.f('ix_worst_created_at'), table_name='worst')
    op.drop_table('worst')
    op.drop_index(op.f('ix_sources_created_at'), table_name='sources')
    op.drop_table('sources')
    op.drop_index(op.f('ix_rules_created_at'), table_name='rules')
    op.drop_table('rules')
    op.drop_index(op.f('ix_grants_created_at'), table_name='grants')
    op.drop_table('grants')
    op.drop_index(op.f('ix_configs_created_at'), table_name='configs')
    op.drop_table('configs')
    op.drop_index(op.f('ix_users_created_at'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_teams_created_at'), table_name='teams')
    op.drop_table('teams')
    op.drop_index(op.f('ix_logs_created_at'), table_name='logs')
    op.drop_table('logs')
