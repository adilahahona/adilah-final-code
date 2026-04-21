"""Add mapped_indicator_values table

Revision ID: 002_mapped_indicators
Revises: 001_initial_schema
Create Date: 2026-02-22 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002_mapped_indicators'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'mapped_indicator_values',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('period_id', sa.Integer(), nullable=False),
        sa.Column('indicator_code', sa.String(length=255), nullable=False),
        sa.Column('numeric_value', sa.Float(), nullable=True),
        sa.Column('unit_normalized', sa.String(length=100), nullable=True),
        sa.Column('pillar', sa.Enum('E', 'S', 'G', 'OTHER', name='pillarenum'), nullable=False),
        sa.Column('raw_indicator_value_ids', sa.JSON(), nullable=True),
        sa.Column('mapping_method', sa.String(length=100), nullable=False),
        sa.Column('mapping_version', sa.String(length=50), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('data_quality_score', sa.Float(), nullable=True),
        sa.Column('extra_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['period_id'], ['reporting_periods.id']),
        sa.ForeignKeyConstraint(['indicator_code'], ['indicator_catalog_items.indicator_code']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_mapped_indicator_values_id'), 'mapped_indicator_values', ['id'])
    op.create_index(op.f('ix_mapped_indicator_values_organization_id'), 'mapped_indicator_values', ['organization_id'])
    op.create_index(op.f('ix_mapped_indicator_values_period_id'), 'mapped_indicator_values', ['period_id'])
    op.create_index(op.f('ix_mapped_indicator_values_indicator_code'), 'mapped_indicator_values', ['indicator_code'])
    op.create_index(op.f('ix_mapped_indicator_values_pillar'), 'mapped_indicator_values', ['pillar'])
    op.create_index('idx_mapped_org_period', 'mapped_indicator_values', ['organization_id', 'period_id'])
    op.create_index('idx_mapped_org_period_pillar', 'mapped_indicator_values', ['organization_id', 'period_id', 'pillar'])


def downgrade() -> None:
    op.drop_table('mapped_indicator_values')
