"""
Database models for documents and manual indicator entries.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.infrastructure.database.base import Base


class Document(Base):
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


class ManualIndicatorEntry(Base):
    """Manually entered indicator values from documents."""
    
    __tablename__ = 'manual_indicator_entries'
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False)
    reporting_period_id = Column(Integer, ForeignKey('reporting_periods.id'), nullable=False)
    indicator_id = Column(Integer, ForeignKey('indicators.id'), nullable=False)
    
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
    indicator = relationship('Indicator')
