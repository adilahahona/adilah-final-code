"""Add ML pipeline tables

Revision ID: 004_ml_pipeline
Revises: 003_feature_schema
Create Date: 2026-02-22 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004_ml_pipeline'
down_revision = '003_feature_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # External ratings table
    op.create_table(
        'external_ratings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('period_id', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(length=100), nullable=False),
        sa.Column('composite_score', sa.Float(), nullable=True),
        sa.Column('risk_label', sa.String(length=50), nullable=True),
        sa.Column('e_score', sa.Float(), nullable=True),
        sa.Column('s_score', sa.Float(), nullable=True),
        sa.Column('g_score', sa.Float(), nullable=True),
        sa.Column('extra_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['period_id'], ['reporting_periods.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_external_ratings_id'), 'external_ratings', ['id'])
    op.create_index('idx_ext_rating_org_period', 'external_ratings', ['organization_id', 'period_id'])
    
    # Dataset snapshots
    op.create_table(
        'dataset_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('snapshot_name', sa.String(length=200), nullable=False),
        sa.Column('feature_schema_version_id', sa.Integer(), nullable=False),
        sa.Column('row_count', sa.Integer(), nullable=True),
        sa.Column('feature_vector_ids', sa.JSON(), nullable=False),
        sa.Column('train_ids', sa.JSON(), nullable=True),
        sa.Column('val_ids', sa.JSON(), nullable=True),
        sa.Column('test_ids', sa.JSON(), nullable=True),
        sa.Column('target_provider', sa.String(length=100), nullable=True),
        sa.Column('extra_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['feature_schema_version_id'], ['feature_schema_versions.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dataset_snapshots_id'), 'dataset_snapshots', ['id'])
    
    # Model versions
    op.create_table(
        'model_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('model_name', sa.String(length=200), nullable=False),
        sa.Column('algorithm', sa.String(length=100), nullable=False),
        sa.Column('hyperparameters', sa.JSON(), nullable=True),
        sa.Column('dataset_snapshot_id', sa.Integer(), nullable=False),
        sa.Column('train_metrics', sa.JSON(), nullable=True),
        sa.Column('val_metrics', sa.JSON(), nullable=True),
        sa.Column('artifact_path', sa.String(length=500), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('extra_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['dataset_snapshot_id'], ['dataset_snapshots.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_model_versions_id'), 'model_versions', ['id'])
    op.create_index(op.f('ix_model_versions_status'), 'model_versions', ['status'])
    
    # Predictions
    op.create_table(
        'predictions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('feature_vector_id', sa.Integer(), nullable=False),
        sa.Column('model_version_id', sa.Integer(), nullable=False),
        sa.Column('composite_score', sa.Float(), nullable=True),
        sa.Column('e_score', sa.Float(), nullable=True),
        sa.Column('s_score', sa.Float(), nullable=True),
        sa.Column('g_score', sa.Float(), nullable=True),
        sa.Column('coverage', sa.Float(), nullable=True),
        sa.Column('extra_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['feature_vector_id'], ['feature_vectors.id']),
        sa.ForeignKeyConstraint(['model_version_id'], ['model_versions.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_predictions_id'), 'predictions', ['id'])
    op.create_index(op.f('ix_predictions_feature_vector_id'), 'predictions', ['feature_vector_id'])
    
    # Prediction drivers (key contributors)
    op.create_table(
        'prediction_drivers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('prediction_id', sa.Integer(), nullable=False),
        sa.Column('feature_name', sa.String(length=255), nullable=False),
        sa.Column('contribution', sa.Float(), nullable=False),
        sa.Column('feature_value', sa.Float(), nullable=True),
        sa.Column('rank', sa.Integer(), nullable=True),
        sa.Column('direction', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['prediction_id'], ['predictions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_prediction_drivers_id'), 'prediction_drivers', ['id'])
    op.create_index(op.f('ix_prediction_drivers_prediction_id'), 'prediction_drivers', ['prediction_id'])
    
    # Scoring config versions
    op.create_table(
        'scoring_config_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('version_name', sa.String(length=100), nullable=False),
        sa.Column('pillar_weights', sa.JSON(), nullable=False),
        sa.Column('indicator_bounds', sa.JSON(), nullable=True),
        sa.Column('normalization_method', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('extra_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scoring_config_versions_id'), 'scoring_config_versions', ['id'])
    op.create_index(op.f('ix_scoring_config_versions_version_name'), 'scoring_config_versions', ['version_name'], unique=True)


def downgrade() -> None:
    op.drop_table('scoring_config_versions')
    op.drop_table('prediction_drivers')
    op.drop_table('predictions')
    op.drop_table('model_versions')
    op.drop_table('dataset_snapshots')
    op.drop_table('external_ratings')
