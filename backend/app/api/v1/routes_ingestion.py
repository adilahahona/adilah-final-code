"""
Ingestion API routes for uploading indicator data.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
import json

from app.db.session import get_db
from app.models.ingestion_schemas import UploadSummary, RejectionReason
from app.domain.ingestion.service import IngestionService


router = APIRouter(prefix="/api/v1/ingestion", tags=["Ingestion"])


@router.post("/uploads", response_model=UploadSummary)
async def upload_indicators(
    file: UploadFile = File(..., description="CSV or XLSX file with indicator data"),
    source_name: str = Form(..., description="Name of the data source"),
    source_type: str = Form(default="csv_upload", description="Type of data source"),
    uploaded_by: str = Form(default=None, description="User identifier"),
    description: str = Form(default=None, description="Source description"),
    allow_partial: bool = Form(default=True, description="Allow partial import of valid rows"),
    db: Session = Depends(get_db)
):
    """
    Upload CSV or XLSX file containing indicator values.
    
    **Required columns:**
    - org_name: Organization name
    - period_start: Period start date (YYYY-MM-DD or similar)
    - period_end: Period end date
    - indicator_code: Indicator code
    - value: Indicator value
    
    **Optional columns:**
    - unit: Unit of measurement
    - source: Source reference
    - notes: Additional notes
    
    **Behavior:**
    - Creates organizations and periods automatically if they don't exist
    - If `allow_partial=true`, inserts valid rows even if some rows have errors
    - Returns detailed rejection report for invalid rows
    """
    # Read file content
    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read file: {str(e)}"
        )
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty"
        )
    
    # Process upload
    service = IngestionService(db)
    
    try:
        upload_batch, errors = service.process_upload(
            file_content=content,
            filename=file.filename,
            source_name=source_name,
            source_type=source_type,
            uploaded_by=uploaded_by,
            description=description,
            allow_partial=allow_partial
        )
        
        # Get document (should be the only one in this batch)
        document = upload_batch.raw_documents[0] if upload_batch.raw_documents else None
        
        summary = UploadSummary(
            upload_batch_id=upload_batch.id,
            rows_received=upload_batch.file_count,  # Total from file
            rows_inserted=upload_batch.row_count,  # Actually inserted
            rows_rejected=len(errors),
            rejection_reasons=[
                RejectionReason(
                    row_number=e.row_number,
                    field=e.field,
                    error=e.error,
                    value=e.value
                )
                for e in errors[:100]  # Limit to first 100 errors
            ],
            document_id=document.id if document else 0,
            checksum=document.checksum_sha256 if document else "",
            message=f"Successfully inserted {upload_batch.row_count} rows. {len(errors)} rows rejected."
        )
        
        return summary
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload processing failed: {str(e)}"
        )
