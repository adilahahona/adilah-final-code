"""
Ingestion service for processing uploads.
"""
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Tuple
from datetime import datetime
import pandas as pd
import logging

from app.models.sql_models import (
    Organization,
    ReportingPeriod,
    DataSource,
    UploadBatch,
    RawDocument,
    RawIndicatorValue
)
from app.domain.ingestion.validators import IndicatorRowValidator, ValidationError
from app.domain.ingestion.parsers import FileParser
from app.domain.audit.service import AuditService

logger = logging.getLogger(__name__)


class IngestionService:
    """Service for ingesting indicator data from files."""
    
    def __init__(self, db: Session):
        self.db = db
        self.validator = IndicatorRowValidator()
        self.audit_service = AuditService(db)
    
    def _get_or_create_organization(self, org_name: str) -> Organization:
        """Get or create organization by name."""
        org = self.db.query(Organization).filter(Organization.name == org_name).first()
        
        if not org:
            org = Organization(name=org_name)
            self.db.add(org)
            self.db.flush()
            
            logger.info(f"Created organization: {org_name} (ID: {org.id})")
        
        return org
    
    def _get_or_create_period(
        self,
        org_id: int,
        period_start: datetime,
        period_end: datetime,
        period_type: str = "annual"
    ) -> ReportingPeriod:
        """Get or create reporting period."""
        period = (
            self.db.query(ReportingPeriod)
            .filter(
                ReportingPeriod.organization_id == org_id,
                ReportingPeriod.period_start == period_start,
                ReportingPeriod.period_end == period_end
            )
            .first()
        )
        
        if not period:
            period = ReportingPeriod(
                organization_id=org_id,
                period_start=period_start,
                period_end=period_end,
                period_type=period_type
            )
            self.db.add(period)
            self.db.flush()
            
            logger.info(f"Created period for org {org_id}: {period_start} to {period_end}")
        
        return period
    
    def _get_or_create_data_source(
        self,
        name: str,
        source_type: str,
        description: str = None
    ) -> DataSource:
        """Get or create data source."""
        source = (
            self.db.query(DataSource)
            .filter(
                DataSource.name == name,
                DataSource.source_type == source_type
            )
            .first()
        )
        
        if not source:
            source = DataSource(
                name=name,
                source_type=source_type,
                description=description
            )
            self.db.add(source)
            self.db.flush()
        
        return source
    
    def process_upload(
        self,
        file_content: bytes,
        filename: str,
        source_name: str,
        source_type: str = "csv_upload",
        uploaded_by: str = None,
        description: str = None,
        allow_partial: bool = True
    ) -> Tuple[UploadBatch, List[ValidationError]]:
        """
        Process uploaded file and ingest indicator values.
        
        Args:
            file_content: File bytes
            filename: Original filename
            source_name: Name of data source
            source_type: Type of source
            uploaded_by: User identifier
            description: Source description
            allow_partial: If True, insert valid rows even if some are rejected
            
        Returns:
            Tuple of (UploadBatch, List of validation errors)
        """
        # Parse file
        try:
            df = FileParser.parse_file(file_content, filename)
        except Exception as e:
            logger.error(f"Failed to parse file {filename}: {str(e)}")
            raise ValueError(f"Failed to parse file: {str(e)}")
        
        # Validate
        validation_result = self.validator.validate_dataframe(df, strict=not allow_partial)
        
        # Create data source
        data_source = self._get_or_create_data_source(
            name=source_name,
            source_type=source_type,
            description=description
        )
        
        # Create upload batch
        upload_batch = UploadBatch(
            data_source_id=data_source.id,
            uploaded_by=uploaded_by,
            upload_timestamp=datetime.utcnow(),
            file_count=1,
            row_count=len(df),
            status="processing"
        )
        self.db.add(upload_batch)
        self.db.flush()
        
        # Compute checksum and store document
        checksum = FileParser.compute_checksum(file_content)
        
        raw_document = RawDocument(
            upload_batch_id=upload_batch.id,
            filename=filename,
            file_size=len(file_content),
            mime_type=self._get_mime_type(filename),
            checksum_sha256=checksum,
            extraction_method="pandas_parser",
            extraction_metadata={"total_rows": len(df)}
        )
        self.db.add(raw_document)
        self.db.flush()
        
        # Process rows
        inserted_count = 0
        rejected_count = 0
        
        for idx, row in df.iterrows():
            # Skip rows with errors if not allowing partial
            if not allow_partial and idx in [e.row_number - 2 for e in validation_result.errors]:
                rejected_count += 1
                continue
            
            # Check if this row has errors
            row_errors = [e for e in validation_result.errors if e.row_number == idx + 2]
            if row_errors:
                rejected_count += 1
                continue
            
            try:
                # Get or create org and period
                org = self._get_or_create_organization(str(row["org_name"]))
                
                period_start = pd.to_datetime(row["period_start"])
                period_end = pd.to_datetime(row["period_end"])
                
                period = self._get_or_create_period(
                    org_id=org.id,
                    period_start=period_start,
                    period_end=period_end
                )
                
                # Parse value
                value_str = str(row["value"])
                numeric_value = None
                try:
                    numeric_value = float(value_str)
                except ValueError:
                    pass  # Keep as text in raw_value
                
                # Create raw indicator value
                raw_value = RawIndicatorValue(
                    organization_id=org.id,
                    period_id=period.id,
                    upload_batch_id=upload_batch.id,
                    source_document_id=raw_document.id,
                    indicator_code=str(row["indicator_code"]),
                    raw_value=value_str,
                    numeric_value=numeric_value,
                    unit=str(row.get("unit")) if pd.notna(row.get("unit")) else None,
                    extraction_method="manual_upload",
                    notes=str(row.get("notes")) if pd.notna(row.get("notes")) else None
                )
                self.db.add(raw_value)
                inserted_count += 1
                
            except Exception as e:
                logger.error(f"Error processing row {idx + 2}: {str(e)}")
                rejected_count += 1
                validation_result.errors.append(ValidationError(
                    row_number=idx + 2,
                    error=f"Processing error: {str(e)}"
                ))
        
        # Update batch status
        upload_batch.status = "completed" if rejected_count == 0 else "partial"
        upload_batch.row_count = inserted_count
        
        self.db.commit()
        
        # Log audit event
        self.audit_service.log_event(
            event_type="ingestion",
            action="upload",
            entity_type="UploadBatch",
            entity_id=upload_batch.id,
            user_id=uploaded_by,
            after_state={
                "filename": filename,
                "rows_inserted": inserted_count,
                "rows_rejected": rejected_count,
                "checksum": checksum
            }
        )
        
        return upload_batch, validation_result.errors
    
    def _get_mime_type(self, filename: str) -> str:
        """Get MIME type from filename."""
        if filename.lower().endswith('.csv'):
            return 'text/csv'
        elif filename.lower().endswith('.xlsx'):
            return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        elif filename.lower().endswith('.xls'):
            return 'application/vnd.ms-excel'
        return 'application/octet-stream'
