"""Add feature schema and vector tables

Revision ID: 003_feature_schema
Revises: 002_mapped_indicators
Create Date: 2026-02-22 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003_feature_schema'
down_revision = '002_mapped_indicators'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Feature schema version table
    op.create_table(
        'feature_schema_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('version_name', sa.String(length=100), nullable=False),
        sa.Column('feature_list', sa.JSON(), nullable=False),
        sa.Column('transforms', sa.JSON(), nullable=True),
        sa.Column('imputation_rules', sa.JSON(), nullable=True),
        sa.Column('scaling_policy', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('extra_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_feature_schema_versions_id'), 'feature_schema_versions', ['id'])
    op.create_index(op.f('ix_feature_schema_versions_version_name'), 'feature_schema_versions', ['version_name'], unique=True)
    op.create_index(op.f('ix_feature_schema_versions_is_active'), 'feature_schema_versions', ['is_active'])
    
    # Feature vector table
    op.create_table(
        'feature_vectors',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('period_id', sa.Integer(), nullable=False),
        sa.Column('schema_version_id', sa.Integer(), nullable=False),
        sa.Column('features', sa.JSON(), nullable=False),
        sa.Column('feature_count', sa.Integer(), nullable=True),
        sa.Column('missing_count', sa.Integer(), nullable=True),
        sa.Column('extra_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['period_id'], ['reporting_periods.id']),
        sa.ForeignKeyConstraint(['schema_version_id'], ['feature_schema_versions.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_feature_vectors_id'), 'feature_vectors', ['id'])
    op.create_index(op.f('ix_feature_vectors_organization_id'), 'feature_vectors', ['organization_id'])
    op.create_index(op.f('ix_feature_vectors_period_id'), 'feature_vectors', ['period_id'])
    op.create_index(op.f('ix_feature_vectors_schema_version_id'), 'feature_vectors', ['schema_version_id'])
    op.create_index('idx_fv_org_period_schema', 'feature_vectors', ['organization_id', 'period_id', 'schema_version_id'], unique=True)


def downgrade() -> None:
    op.drop_table('feature_vectors')
    op.drop_table('feature_schema_versions')
