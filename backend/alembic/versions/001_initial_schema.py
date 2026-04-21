"""Initial database schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-02-22 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create organizations table
    op.create_table(
        'organizations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('external_id', sa.String(length=100), nullable=True),
        sa.Column('sector', sa.String(length=100), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('extra_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organizations_id'), 'organizations', ['id'])
    op.create_index(op.f('ix_organizations_name'), 'organizations', ['name'], unique=True)
    op.create_index(op.f('ix_organizations_external_id'), 'organizations', ['external_id'], unique=True)
    
    # Create reporting_periods table
    op.create_table(
        'reporting_periods',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('period_type', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reporting_periods_id'), 'reporting_periods', ['id'])
    op.create_index(op.f('ix_reporting_periods_organization_id'), 'reporting_periods', ['organization_id'])
    op.create_index('idx_org_period', 'reporting_periods', ['organization_id', 'period_start', 'period_end'])
    
    # Create data_sources table
    op.create_table(
        'data_sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('source_type', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('url', sa.Text(), nullable=True),
        sa.Column('extra_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_data_sources_id'), 'data_sources', ['id'])
    
    # Create upload_batches table
    op.create_table(
        'upload_batches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('data_source_id', sa.Integer(), nullable=False),
        sa.Column('uploaded_by', sa.String(length=255), nullable=True),
        sa.Column('upload_timestamp', sa.DateTime(), nullable=False),
        sa.Column('file_count', sa.Integer(), nullable=True),
        sa.Column('row_count', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('extra_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['data_source_id'], ['data_sources.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_upload_batches_id'), 'upload_batches', ['id'])
    op.create_index(op.f('ix_upload_batches_data_source_id'), 'upload_batches', ['data_source_id'])
    
    # Create raw_documents table
    op.create_table(
        'raw_documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('upload_batch_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('checksum_sha256', sa.String(length=64), nullable=False),
        sa.Column('file_path', sa.Text(), nullable=True),
        sa.Column('file_content', sa.LargeBinary(), nullable=True),
        sa.Column('extraction_method', sa.String(length=100), nullable=True),
        sa.Column('extraction_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['upload_batch_id'], ['upload_batches.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_raw_documents_id'), 'raw_documents', ['id'])
    op.create_index(op.f('ix_raw_documents_upload_batch_id'), 'raw_documents', ['upload_batch_id'])
    op.create_index(op.f('ix_raw_documents_checksum_sha256'), 'raw_documents', ['checksum_sha256'])
    
    # Create indicator_catalog_items table
    op.create_table(
        'indicator_catalog_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('indicator_code', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('pillar', sa.Enum('E', 'S', 'G', 'OTHER', name='pillarenum'), nullable=False),
        sa.Column('unit', sa.String(length=100), nullable=True),
        sa.Column('data_type', sa.String(length=50), nullable=False),
        sa.Column('is_required', sa.Boolean(), nullable=True),
        sa.Column('aliases', sa.JSON(), nullable=True),
        sa.Column('validation_rules', sa.JSON(), nullable=True),
        sa.Column('extra_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_indicator_catalog_items_id'), 'indicator_catalog_items', ['id'])
    op.create_index(op.f('ix_indicator_catalog_items_indicator_code'), 'indicator_catalog_items', ['indicator_code'], unique=True)
    op.create_index(op.f('ix_indicator_catalog_items_pillar'), 'indicator_catalog_items', ['pillar'])
    
    # Create raw_indicator_values table
    op.create_table(
        'raw_indicator_values',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('period_id', sa.Integer(), nullable=False),
        sa.Column('upload_batch_id', sa.Integer(), nullable=False),
        sa.Column('source_document_id', sa.Integer(), nullable=True),
        sa.Column('indicator_code', sa.String(length=255), nullable=False),
        sa.Column('raw_value', sa.Text(), nullable=False),
        sa.Column('numeric_value', sa.Float(), nullable=True),
        sa.Column('unit', sa.String(length=100), nullable=True),
        sa.Column('extraction_method', sa.String(length=100), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('extra_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['period_id'], ['reporting_periods.id']),
        sa.ForeignKeyConstraint(['upload_batch_id'], ['upload_batches.id']),
        sa.ForeignKeyConstraint(['source_document_id'], ['raw_documents.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_raw_indicator_values_id'), 'raw_indicator_values', ['id'])
    op.create_index(op.f('ix_raw_indicator_values_organization_id'), 'raw_indicator_values', ['organization_id'])
    op.create_index(op.f('ix_raw_indicator_values_period_id'), 'raw_indicator_values', ['period_id'])
    op.create_index(op.f('ix_raw_indicator_values_upload_batch_id'), 'raw_indicator_values', ['upload_batch_id'])
    op.create_index(op.f('ix_raw_indicator_values_source_document_id'), 'raw_indicator_values', ['source_document_id'])
    op.create_index(op.f('ix_raw_indicator_values_indicator_code'), 'raw_indicator_values', ['indicator_code'])
    op.create_index('idx_org_period_indicator', 'raw_indicator_values', ['organization_id', 'period_id', 'indicator_code'])
    
    # Create framework_mappings table
    op.create_table(
        'framework_mappings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('framework_name', sa.String(length=100), nullable=False),
        sa.Column('framework_item_id', sa.String(length=255), nullable=False),
        sa.Column('framework_item_name', sa.String(length=500), nullable=True),
        sa.Column('indicator_code', sa.String(length=255), nullable=False),
        sa.Column('relevance_weight', sa.Float(), nullable=True),
        sa.Column('mapping_rationale', sa.Text(), nullable=True),
        sa.Column('mapping_version', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['indicator_code'], ['indicator_catalog_items.indicator_code']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_framework_mappings_id'), 'framework_mappings', ['id'])
    op.create_index(op.f('ix_framework_mappings_framework_name'), 'framework_mappings', ['framework_name'])
    op.create_index(op.f('ix_framework_mappings_indicator_code'), 'framework_mappings', ['indicator_code'])
    op.create_index('idx_framework_item', 'framework_mappings', ['framework_name', 'framework_item_id'], unique=True)
    
    # Create audit_events table (append-only, no updated_at)
    op.create_table(
        'audit_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=100), nullable=True),
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.String(length=255), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('before_state', sa.JSON(), nullable=True),
        sa.Column('after_state', sa.JSON(), nullable=True),
        sa.Column('changes', sa.JSON(), nullable=True),
        sa.Column('request_id', sa.String(length=100), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('extra_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_events_id'), 'audit_events', ['id'])
    op.create_index(op.f('ix_audit_events_event_type'), 'audit_events', ['event_type'])
    op.create_index(op.f('ix_audit_events_entity_type'), 'audit_events', ['entity_type'])
    op.create_index(op.f('ix_audit_events_user_id'), 'audit_events', ['user_id'])
    op.create_index(op.f('ix_audit_events_request_id'), 'audit_events', ['request_id'])
    op.create_index('idx_created_at', 'audit_events', ['created_at'])
    op.create_index('idx_event_entity', 'audit_events', ['event_type', 'entity_type', 'entity_id'])


def downgrade() -> None:
    op.drop_table('audit_events')
    op.drop_table('framework_mappings')
    op.drop_table('raw_indicator_values')
    op.drop_table('indicator_catalog_items')
    op.drop_table('raw_documents')
    op.drop_table('upload_batches')
    op.drop_table('data_sources')
    op.drop_table('reporting_periods')
    op.drop_table('organizations')
    op.execute('DROP TYPE IF EXISTS pillarenum')
