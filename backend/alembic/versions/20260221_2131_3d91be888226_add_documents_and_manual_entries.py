"""add_documents_and_manual_entries

Revision ID: 3d91be888226
Revises: 004_ml_pipeline
Create Date: 2026-02-21 21:31:42.030061+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3d91be888226'
down_revision = '004_ml_pipeline'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create documents table
    op.create_table(
        'documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('reporting_period_id', sa.Integer(), nullable=True),
        sa.Column('filename', sa.String(length=500), nullable=False),
        sa.Column('file_path', sa.String(length=1000), nullable=False),
        sa.Column('file_size_bytes', sa.Integer(), nullable=False),
        sa.Column('content_type', sa.String(length=100), nullable=True),
        sa.Column('total_pages', sa.Integer(), nullable=True),
        sa.Column('total_words', sa.Integer(), nullable=True),
        sa.Column('pdf_metadata', sa.JSON(), nullable=True),
        sa.Column('parsing_status', sa.String(length=50), nullable=True),
        sa.Column('parsing_error', sa.Text(), nullable=True),
        sa.Column('full_text', sa.Text(), nullable=True),
        sa.Column('uploaded_by', sa.String(length=200), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(), nullable=False),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['reporting_period_id'], ['reporting_periods.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_documents_id'), 'documents', ['id'], unique=False)
    
    # Create manual_indicator_entries table
    op.create_table(
        'manual_indicator_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('reporting_period_id', sa.Integer(), nullable=False),
        sa.Column('indicator_id', sa.Integer(), nullable=False),
        sa.Column('value_numeric', sa.Float(), nullable=True),
        sa.Column('value_text', sa.Text(), nullable=True),
        sa.Column('value_boolean', sa.String(length=10), nullable=True),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('location_context', sa.Text(), nullable=True),
        sa.Column('entered_by', sa.String(length=200), nullable=False),
        sa.Column('entered_at', sa.DateTime(), nullable=False),
        sa.Column('verified_by', sa.String(length=200), nullable=True),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('confidence', sa.String(length=20), nullable=True),
        sa.Column('requires_review', sa.String(length=10), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.ForeignKeyConstraint(['reporting_period_id'], ['reporting_periods.id'], ),
        sa.ForeignKeyConstraint(['indicator_id'], ['indicator_catalog_items.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_manual_indicator_entries_id'), 'manual_indicator_entries', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_manual_indicator_entries_id'), table_name='manual_indicator_entries')
    op.drop_table('manual_indicator_entries')
    op.drop_index(op.f('ix_documents_id'), table_name='documents')
    op.drop_table('documents')
