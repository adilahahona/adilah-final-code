"""
SQLAlchemy models for ESG Analytics System.
All core entities for data ingestion, mapping, and audit.
"""
from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime, Boolean,
    ForeignKey, Index, JSON, LargeBinary, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.base import Base, TimestampMixin, AuditMixin


class Organization(Base, TimestampMixin):
    """
    Organization entity representing companies/entities being assessed.
    """
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    external_id = Column(String(100), unique=True, nullable=True, index=True)
    sector = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    extra_metadata = Column(JSON, nullable=True)
    
    # Relationships
    periods = relationship("ReportingPeriod", back_populates="organization", cascade="all, delete-orphan")
    raw_indicator_values = relationship("RawIndicatorValue", back_populates="organization")
    documents = relationship("Document", back_populates="organization")


class ReportingPeriod(Base, TimestampMixin):
    """
    Reporting period for an organization (typically fiscal year or calendar year).
    """
    __tablename__ = "reporting_periods"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    period_type = Column(String(50), default="annual", nullable=False)  # annual, quarterly, etc.
    
    # Relationships
    organization = relationship("Organization", back_populates="periods")
    raw_indicator_values = relationship("RawIndicatorValue", back_populates="period")
    documents = relationship("Document", back_populates="reporting_period")
    manual_entries = relationship("ManualIndicatorEntry", back_populates="reporting_period")
    
    # Composite index for queries
    __table_args__ = (
        Index("idx_org_period", "organization_id", "period_start", "period_end"),
    )


class DataSource(Base, TimestampMixin):
    """
    Data source metadata (e.g., "GRI Report 2023", "SASB Disclosure", "World Bank").
    """
    __tablename__ = "data_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    source_type = Column(String(100), nullable=False)  # manual, csv_upload, pdf_extract, api, etc.
    description = Column(Text, nullable=True)
    url = Column(Text, nullable=True)
    extra_metadata = Column(JSON, nullable=True)
    
    # Relationships
    upload_batches = relationship("UploadBatch", back_populates="data_source")


class UploadBatch(Base, TimestampMixin):
    """
    Groups uploaded data with provenance tracking.
    Each upload creates a batch linking to source and user.
    """
    __tablename__ = "upload_batches"
    
    id = Column(Integer, primary_key=True, index=True)
    data_source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=False, index=True)
    uploaded_by = Column(String(255), nullable=True)  # User identifier
    upload_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    file_count = Column(Integer, default=0)
    row_count = Column(Integer, default=0)
    status = Column(String(50), default="processing")  # processing, completed, failed
    error_message = Column(Text, nullable=True)
    extra_metadata = Column(JSON, nullable=True)
    
    # Relationships
    data_source = relationship("DataSource", back_populates="upload_batches")
    raw_documents = relationship("RawDocument", back_populates="upload_batch")
    raw_indicator_values = relationship("RawIndicatorValue", back_populates="upload_batch")


class RawDocument(Base, TimestampMixin):
    """
    Stores uploaded documents (PDF, CSV, XLSX, etc.) with checksums.
    """
    __tablename__ = "raw_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    upload_batch_id = Column(Integer, ForeignKey("upload_batches.id"), nullable=False, index=True)
    filename = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)  # bytes
    mime_type = Column(String(100), nullable=True)
    checksum_sha256 = Column(String(64), nullable=False, index=True)
    file_path = Column(Text, nullable=True)  # Storage path if file is saved
    file_content = Column(LargeBinary, nullable=True)  # Optional: store small files
    extraction_method = Column(String(100), nullable=True)
    extraction_metadata = Column(JSON, nullable=True)
    
    # Relationships
    upload_batch = relationship("UploadBatch", back_populates="raw_documents")
    raw_indicator_values = relationship("RawIndicatorValue", back_populates="source_document")


class RawIndicatorValue(Base, TimestampMixin):
    """
    Raw indicator values extracted from uploads.
    Stores original values before mapping and normalization.
    """
    __tablename__ = "raw_indicator_values"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    period_id = Column(Integer, ForeignKey("reporting_periods.id"), nullable=False, index=True)
    upload_batch_id = Column(Integer, ForeignKey("upload_batches.id"), nullable=False, index=True)
    source_document_id = Column(Integer, ForeignKey("raw_documents.id"), nullable=True, index=True)
    
    # Indicator details
    indicator_code = Column(String(255), nullable=False, index=True)
    raw_value = Column(Text, nullable=False)  # Store as text, parse later
    numeric_value = Column(Float, nullable=True)  # Parsed numeric value
    unit = Column(String(100), nullable=True)
    
    # Provenance
    extraction_method = Column(String(100), nullable=True)  # manual, parser_v1, etc.
    confidence = Column(Float, nullable=True)  # 0.0 to 1.0
    notes = Column(Text, nullable=True)
    extra_metadata = Column(JSON, nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="raw_indicator_values")
    period = relationship("ReportingPeriod", back_populates="raw_indicator_values")
    upload_batch = relationship("UploadBatch", back_populates="raw_indicator_values")
    source_document = relationship("RawDocument", back_populates="raw_indicator_values")
    
    # Composite indexes for queries
    __table_args__ = (
        Index("idx_org_period_indicator", "organization_id", "period_id", "indicator_code"),
    )


class PillarEnum(str, enum.Enum):
    """ESG Pillars."""
    E = "E"
    S = "S"
    G = "G"
    OTHER = "OTHER"


class IndicatorCatalogItem(Base, TimestampMixin):
    """
    Canonical catalog of ESG indicators.
    Defines standardized indicators across frameworks.
    """
    __tablename__ = "indicator_catalog_items"
    
    id = Column(Integer, primary_key=True, index=True)
    indicator_code = Column(String(255), nullable=False, unique=True, index=True)
    name = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    pillar = Column(SQLEnum(PillarEnum), nullable=False, index=True)
    unit = Column(String(100), nullable=True)
    data_type = Column(String(50), nullable=False, default="numeric")  # numeric, boolean, text
    is_required = Column(Boolean, default=False)  # Required for scoring
    aliases = Column(JSON, nullable=True)  # List of alternative codes/names
    validation_rules = Column(JSON, nullable=True)
    extra_metadata = Column(JSON, nullable=True)
    
    # Relationships
    framework_mappings = relationship("FrameworkMapping", back_populates="catalog_item")


class FrameworkMapping(Base, TimestampMixin):
    """
    Maps framework-specific items to canonical indicators.
    Supports GRI, SASB, TCFD, etc.
    """
    __tablename__ = "framework_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    framework_name = Column(String(100), nullable=False, index=True)  # GRI, SASB, TCFD, etc.
    framework_item_id = Column(String(255), nullable=False)  # Framework-specific identifier
    framework_item_name = Column(String(500), nullable=True)
    indicator_code = Column(String(255), ForeignKey("indicator_catalog_items.indicator_code"), nullable=False, index=True)
    
    # Mapping metadata
    relevance_weight = Column(Float, default=1.0)  # How relevant this mapping is (0.0 to 1.0)
    mapping_rationale = Column(Text, nullable=True)
    mapping_version = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    catalog_item = relationship("IndicatorCatalogItem", back_populates="framework_mappings")
    
    # Composite unique constraint
    __table_args__ = (
        Index("idx_framework_item", "framework_name", "framework_item_id", unique=True),
    )


class AuditEvent(Base, AuditMixin):
    """
    Immutable audit log for all significant actions.
    NO updated_at - append-only.
    """
    __tablename__ = "audit_events"
    
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(100), nullable=True, index=True)
    entity_id = Column(Integer, nullable=True)
    user_id = Column(String(255), nullable=True, index=True)
    action = Column(String(100), nullable=False)  # create, update, delete, approve, etc.
    
    # Event details
    before_state = Column(JSON, nullable=True)
    after_state = Column(JSON, nullable=True)
    changes = Column(JSON, nullable=True)
    
    # Context
    request_id = Column(String(100), nullable=True, index=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    extra_metadata = Column(JSON, nullable=True)
    
    # Index for time-based queries
    __table_args__ = (
        Index("idx_created_at", "created_at"),
        Index("idx_event_entity", "event_type", "entity_type", "entity_id"),
    )


class MappedIndicatorValue(Base, TimestampMixin):
    """
    Canonical indicator values after mapping and normalization.
    """
    __tablename__ = "mapped_indicator_values"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    period_id = Column(Integer, ForeignKey("reporting_periods.id"), nullable=False, index=True)
    indicator_code = Column(String(255), ForeignKey("indicator_catalog_items.indicator_code"), nullable=False, index=True)
    
    # Mapped value
    numeric_value = Column(Float, nullable=True)
    unit_normalized = Column(String(100), nullable=True)  # Normalized unit
    pillar = Column(SQLEnum(PillarEnum), nullable=False, index=True)
    
    # Provenance
    raw_indicator_value_ids = Column(JSON, nullable=True)  # List of source raw value IDs
    mapping_method = Column(String(100), nullable=False)  # direct, aliased, framework
    mapping_version = Column(String(50), nullable=True)
    
    # Quality
    confidence = Column(Float, nullable=True)
    data_quality_score = Column(Float, nullable=True)
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True)
    
    # Composite indexes
    __table_args__ = (
        Index("idx_mapped_org_period", "organization_id", "period_id"),
        Index("idx_mapped_org_period_pillar", "organization_id", "period_id", "pillar"),
    )


class FeatureSchemaVersion(Base, TimestampMixin):
    """
    Frozen feature schema definition.
    Immutable after creation to ensure reproducibility.
    """
    __tablename__ = "feature_schema_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    version_name = Column(String(100), nullable=False, unique=True, index=True)
    feature_list = Column(JSON, nullable=False)  # List of feature names
    transforms = Column(JSON, nullable=True)  # Transform definitions
    imputation_rules = Column(JSON, nullable=True)  # Imputation strategies
    scaling_policy = Column(String(100), nullable=True)  # standard, minmax, none
    is_active = Column(Boolean, default=True, index=True)
    description = Column(Text, nullable=True)
    extra_metadata = Column(JSON, nullable=True)
    
    # Relationships
    feature_vectors = relationship("FeatureVector", back_populates="schema_version")


class FeatureVector(Base, TimestampMixin):
    """
    Feature vector for an organization-period pair.
    Links to a specific schema version for reproducibility.
    """
    __tablename__ = "feature_vectors"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    period_id = Column(Integer, ForeignKey("reporting_periods.id"), nullable=False, index=True)
    schema_version_id = Column(Integer, ForeignKey("feature_schema_versions.id"), nullable=False, index=True)
    
    # Features as JSON dictionary
    features = Column(JSON, nullable=False)
    feature_count = Column(Integer, nullable=True)
    missing_count = Column(Integer, nullable=True)
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True)
    
    # Relationships
    schema_version = relationship("FeatureSchemaVersion", back_populates="feature_vectors")
    
    # Unique constraint: one vector per org-period-schema combo
    __table_args__ = (
        Index("idx_fv_org_period_schema", "organization_id", "period_id", "schema_version_id", unique=True),
    )


class ExternalRating(Base, TimestampMixin):
    """External ESG ratings from third-party providers."""
    __tablename__ = "external_ratings"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    period_id = Column(Integer, ForeignKey("reporting_periods.id"), nullable=False)
    provider = Column(String(100), nullable=False)
    composite_score = Column(Float, nullable=True)
    risk_label = Column(String(50), nullable=True)
    e_score = Column(Float, nullable=True)
    s_score = Column(Float, nullable=True)
    g_score = Column(Float, nullable=True)
    extra_metadata = Column(JSON, nullable=True)
    
    __table_args__ = (
        Index("idx_ext_rating_org_period", "organization_id", "period_id"),
    )


class DatasetSnapshot(Base, TimestampMixin):
    """Immutable snapshot of training dataset."""
    __tablename__ = "dataset_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    snapshot_name = Column(String(200), nullable=False)
    feature_schema_version_id = Column(Integer, ForeignKey("feature_schema_versions.id"), nullable=False)
    row_count = Column(Integer, nullable=True)
    feature_vector_ids = Column(JSON, nullable=False)
    train_ids = Column(JSON, nullable=True)
    val_ids = Column(JSON, nullable=True)
    test_ids = Column(JSON, nullable=True)
    target_provider = Column(String(100), nullable=True)
    extra_metadata = Column(JSON, nullable=True)


class ModelVersion(Base, TimestampMixin):
    """Tracked model version with full provenance."""
    __tablename__ = "model_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(200), nullable=False)
    algorithm = Column(String(100), nullable=False)
    hyperparameters = Column(JSON, nullable=True)
    dataset_snapshot_id = Column(Integer, ForeignKey("dataset_snapshots.id"), nullable=False)
    train_metrics = Column(JSON, nullable=True)
    val_metrics = Column(JSON, nullable=True)
    artifact_path = Column(String(500), nullable=True)
    artifact_checksum = Column(String(64), nullable=True)  # SHA256 checksum for security
    status = Column(String(50), nullable=False, index=True)  # TRAINED, APPROVED, DEPRECATED
    description = Column(Text, nullable=True)
    extra_metadata = Column(JSON, nullable=True)


class Prediction(Base):
    """Prediction output from a model version."""
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    feature_vector_id = Column(Integer, ForeignKey("feature_vectors.id"), nullable=False, index=True)
    model_version_id = Column(Integer, ForeignKey("model_versions.id"), nullable=False)
    composite_score = Column(Float, nullable=True)
    e_score = Column(Float, nullable=True)
    s_score = Column(Float, nullable=True)
    g_score = Column(Float, nullable=True)
    coverage = Column(Float, nullable=True)
    extra_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    feature_vector = relationship("FeatureVector")
    drivers = relationship("PredictionDriver", back_populates="prediction", cascade="all, delete-orphan")


class PredictionDriver(Base):
    """Key feature contributions to a prediction."""
    __tablename__ = "prediction_drivers"
    
    id = Column(Integer, primary_key=True, index=True)
    prediction_id = Column(Integer, ForeignKey("predictions.id", ondelete="CASCADE"), nullable=False, index=True)
    feature_name = Column(String(255), nullable=False)
    contribution = Column(Float, nullable=False)
    feature_value = Column(Float, nullable=True)
    rank = Column(Integer, nullable=True)
    direction = Column(String(20), nullable=True)  # positive, negative
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    prediction = relationship("Prediction", back_populates="drivers")


class ScoringConfigVersion(Base, TimestampMixin):
    """Scoring configuration for deterministic ESG subscores."""
    __tablename__ = "scoring_config_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    version_name = Column(String(100), nullable=False, unique=True)
    pillar_weights = Column(JSON, nullable=False)  # {E: 0.33, S: 0.33, G: 0.34}
    indicator_bounds = Column(JSON, nullable=True)  # Min/max for normalization
    normalization_method = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)


class Document(Base, TimestampMixin):
    """Uploaded ESG report documents (PDFs)."""
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False)
    reporting_period_id = Column(Integer, ForeignKey('reporting_periods.id'), nullable=True)
    
    filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)  # Path to stored file
    file_size_bytes = Column(Integer, nullable=False)
    content_type = Column(String(100), default='application/pdf')
    
    # PDF metadata
    total_pages = Column(Integer)
    total_words = Column(Integer)
    pdf_metadata = Column(JSON)  # Author, title, creation date, etc.
    
    # Processing status
    parsing_status = Column(String(50), default='pending')  # pending, success, failed
    parsing_error = Column(Text)
    full_text = Column(Text)  # Extracted text content
    
    uploaded_by = Column(String(200))  # User who uploaded
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime)
    
    # Relationships
    organization = relationship('Organization', back_populates='documents')
    reporting_period = relationship('ReportingPeriod', back_populates='documents')
    manual_entries = relationship('ManualIndicatorEntry', back_populates='document')


class ManualIndicatorEntry(Base, TimestampMixin):
    """Manually entered indicator values from documents."""
    __tablename__ = 'manual_indicator_entries'
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False)
    reporting_period_id = Column(Integer, ForeignKey('reporting_periods.id'), nullable=False)
    indicator_id = Column(Integer, ForeignKey('indicator_catalog_items.id'), nullable=False)
    
    # The manually entered value
    value_numeric = Column(Float)
    value_text = Column(Text)
    value_boolean = Column(String(10))  # 'true', 'false', 'yes', 'no'
    
    # Source information
    page_number = Column(Integer)  # Page in the PDF where value was found
    location_context = Column(Text)  # Surrounding text for verification
    
    # Entry metadata
    entered_by = Column(String(200), nullable=False)
    entered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    verified_by = Column(String(200))
    verified_at = Column(DateTime)
    notes = Column(Text)
    
    # Quality flags
    confidence = Column(String(20))  # high, medium, low
    requires_review = Column(String(10), default='false')
    
    # Relationships
    document = relationship('Document', back_populates='manual_entries')
    reporting_period = relationship('ReportingPeriod', back_populates='manual_entries')
    # indicator = relationship('Indicator')  # Commented out - Indicator model doesn't exist
    description = Column(Text, nullable=True)
    extra_metadata = Column(JSON, nullable=True)
