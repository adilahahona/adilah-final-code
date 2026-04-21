"""
API routes for document upload and management.
Handles PDF uploads, text extraction, NLP analysis, and manual indicator entry.
"""
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Form, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pathlib import Path
import shutil
import logging
from datetime import datetime

from app.db.session import get_db
from app.models.sql_models import Document, ManualIndicatorEntry, Organization, ReportingPeriod
from app.domain.ingestion.pdf_parser import PDFParser
from app.domain.nlp.service import score_text
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

# Storage directory for uploaded files
UPLOAD_DIR = Path("./uploads/documents")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# Pydantic schemas
class DocumentResponse(BaseModel):
    id: int
    organization_id: int
    reporting_period_id: Optional[int]
    filename: str
    file_size_bytes: int
    content_type: str
    total_pages: Optional[int]
    total_words: Optional[int]
    parsing_status: str
    parsing_error: Optional[str]
    uploaded_by: Optional[str]
    uploaded_at: datetime
    processed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ManualEntryCreate(BaseModel):
    document_id: int
    reporting_period_id: int
    indicator_id: int
    value_numeric: Optional[float] = None
    value_text: Optional[str] = None
    value_boolean: Optional[str] = None
    page_number: Optional[int] = None
    location_context: Optional[str] = None
    entered_by: str
    notes: Optional[str] = None
    confidence: str = "medium"  # high, medium, low


class ManualEntryResponse(BaseModel):
    id: int
    document_id: int
    reporting_period_id: int
    indicator_id: int
    value_numeric: Optional[float]
    value_text: Optional[str]
    value_boolean: Optional[str]
    page_number: Optional[int]
    location_context: Optional[str]
    entered_by: str
    entered_at: datetime
    verified_by: Optional[str]
    verified_at: Optional[datetime]
    notes: Optional[str]
    confidence: str
    requires_review: str
    
    class Config:
        from_attributes = True


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    organization_id: int = Form(...),
    reporting_period_id: Optional[int] = Form(None),
    uploaded_by: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload a PDF document for an organization.
    The document will be parsed and text extracted automatically.
    """
    # Validate organization exists
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail=f"Organization {organization_id} not found")
    
    # Validate reporting period if provided
    if reporting_period_id:
        period = db.query(ReportingPeriod).filter(ReportingPeriod.id == reporting_period_id).first()
        if not period:
            raise HTTPException(status_code=404, detail=f"Reporting period {reporting_period_id} not found")
        if period.organization_id != organization_id:
            raise HTTPException(status_code=400, detail="Reporting period does not belong to organization")
    
    # Validate file type
    if not file.content_type == "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Generate unique filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{organization_id}_{timestamp}_{file.filename}"
    file_path = UPLOAD_DIR / safe_filename
    
    # Save file
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        file_size = file_path.stat().st_size
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Create database record
    doc = Document(
        organization_id=organization_id,
        reporting_period_id=reporting_period_id,
        filename=file.filename or "unknown.pdf",
        file_path=str(file_path),
        file_size_bytes=file_size,
        content_type=file.content_type or "application/pdf",
        parsing_status="pending",
        uploaded_by=uploaded_by,
        uploaded_at=datetime.utcnow()
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    
    # Parse PDF asynchronously (in real app, use celery/background task)
    try:
        parser = PDFParser()
        parsed_data = parser.parse(file_path)
        
        # Update document with parsed data
        doc.total_pages = parsed_data['total_pages']
        doc.total_words = parsed_data['total_words']
        doc.pdf_metadata = parsed_data['metadata']
        doc.full_text = parsed_data['full_text']
        doc.parsing_status = "success"
        doc.processed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(doc)
    except Exception as e:
        doc.parsing_status = "failed"
        doc.parsing_error = str(e)
        doc.processed_at = datetime.utcnow()
        db.commit()
        db.refresh(doc)
    
    return doc


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: int, db: Session = Depends(get_db)):
    """Get document details by ID."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")
    return doc


@router.get("/", response_model=List[DocumentResponse])
def list_documents(
    organization_id: Optional[int] = None,
    reporting_period_id: Optional[int] = None,
    parsing_status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List documents with optional filters."""
    query = db.query(Document)
    
    if organization_id:
        query = query.filter(Document.organization_id == organization_id)
    if reporting_period_id:
        query = query.filter(Document.reporting_period_id == reporting_period_id)
    if parsing_status:
        query = query.filter(Document.parsing_status == parsing_status)
    
    return query.order_by(Document.uploaded_at.desc()).all()


@router.get("/{document_id}/text")
def get_document_text(document_id: int, db: Session = Depends(get_db)):
    """Get the full extracted text from a document."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")
    
    if doc.parsing_status != "success":
        raise HTTPException(status_code=400, detail=f"Document parsing status: {doc.parsing_status}")
    
    return {"document_id": document_id, "filename": doc.filename, "full_text": doc.full_text}


@router.post("/manual-entries", response_model=ManualEntryResponse)
def create_manual_entry(entry: ManualEntryCreate, db: Session = Depends(get_db)):
    """Create a manual indicator entry from a document."""
    # Validate document exists
    doc = db.query(Document).filter(Document.id == entry.document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {entry.document_id} not found")
    
    # Create entry
    manual_entry = ManualIndicatorEntry(**entry.dict())
    db.add(manual_entry)
    db.commit()
    db.refresh(manual_entry)
    
    return manual_entry


@router.get("/manual-entries/", response_model=List[ManualEntryResponse])
def list_manual_entries(
    document_id: Optional[int] = None,
    reporting_period_id: Optional[int] = None,
    indicator_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """List manual indicator entries with optional filters."""
    query = db.query(ManualIndicatorEntry)
    
    if document_id:
        query = query.filter(ManualIndicatorEntry.document_id == document_id)
    if reporting_period_id:
        query = query.filter(ManualIndicatorEntry.reporting_period_id == reporting_period_id)
    if indicator_id:
        query = query.filter(ManualIndicatorEntry.indicator_id == indicator_id)
    
    return query.order_by(ManualIndicatorEntry.entered_at.desc()).all()


@router.get("/manual-entries/{entry_id}", response_model=ManualEntryResponse)
def get_manual_entry(entry_id: int, db: Session = Depends(get_db)):
    """Get a specific manual entry."""
    entry = db.query(ManualIndicatorEntry).filter(ManualIndicatorEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail=f"Manual entry {entry_id} not found")
    return entry


@router.delete("/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db)):
    """Delete a document and its associated file."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")

    # Delete file from filesystem
    file_path = Path(doc.file_path)
    if file_path.exists():
        file_path.unlink()

    # Delete database record (cascade will delete manual entries)
    db.delete(doc)
    db.commit()

    return {"success": True, "message": f"Document {document_id} deleted"}


# ---------------------------------------------------------------------------
# Analysis response model
# ---------------------------------------------------------------------------

class AnalysisResult(BaseModel):
    document_id: int
    filename: str
    total_pages: Optional[int]
    total_words: Optional[int]
    composite_score: Optional[float]
    e_score: Optional[float]
    s_score: Optional[float]
    g_score: Optional[float]
    raw_scores: Optional[Dict[str, float]]
    zone_breakdown: Optional[Dict[str, float]]
    model_info: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


def _run_analysis(doc: Document, framework: str = "gri") -> dict:
    """Run NLP analysis on an already-parsed document and return result dict."""
    if doc.parsing_status != "success" or not doc.full_text:
        raise HTTPException(
            status_code=400,
            detail=f"Document text not available (parsing_status={doc.parsing_status})"
        )

    nlp_result = score_text(doc.full_text, framework=framework)

    return {
        "document_id": doc.id,
        "filename": doc.filename,
        "total_pages": doc.total_pages,
        "total_words": doc.total_words,
        "composite_score": nlp_result["composite"],
        "e_score": nlp_result["scaled"].get("E"),
        "s_score": nlp_result["scaled"].get("S"),
        "g_score": nlp_result["scaled"].get("G"),
        "raw_scores": nlp_result["raw"],
        "zone_breakdown": nlp_result["zone_breakdown"],
        "model_info": nlp_result["model_info"],
    }


# ---------------------------------------------------------------------------
# Upload + analyse in one call
# ---------------------------------------------------------------------------

@router.post("/upload-and-analyze", response_model=AnalysisResult)
async def upload_and_analyze(
    file: UploadFile = File(...),
    organization_id: int = Form(...),
    framework: str = Form("gri"),
    reporting_period_id: Optional[int] = Form(None),
    uploaded_by: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """
    Upload a PDF ESG report, extract full text, and immediately run
    NLP-based E/S/G scoring on the entire document.

    Returns the analysis result with composite + pillar scores and
    per-zone keyword breakdown.
    """
    # --- validate org ---
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail=f"Organization {organization_id} not found")

    if reporting_period_id:
        period = db.query(ReportingPeriod).filter(ReportingPeriod.id == reporting_period_id).first()
        if not period:
            raise HTTPException(status_code=404, detail=f"Reporting period {reporting_period_id} not found")
        if period.organization_id != organization_id:
            raise HTTPException(status_code=400, detail="Reporting period does not belong to organization")

    # --- validate file type ---
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # --- save file ---
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{organization_id}_{timestamp}_{file.filename}"
    file_path = UPLOAD_DIR / safe_filename

    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        file_size = file_path.stat().st_size
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # --- create DB record ---
    doc = Document(
        organization_id=organization_id,
        reporting_period_id=reporting_period_id,
        filename=file.filename or "unknown.pdf",
        file_path=str(file_path),
        file_size_bytes=file_size,
        content_type=file.content_type or "application/pdf",
        parsing_status="pending",
        uploaded_by=uploaded_by,
        uploaded_at=datetime.utcnow(),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # --- extract text ---
    try:
        parser = PDFParser()
        parsed_data = parser.parse(file_path)
        doc.total_pages = parsed_data["total_pages"]
        doc.total_words = parsed_data["total_words"]
        doc.pdf_metadata = parsed_data["metadata"]
        doc.full_text = parsed_data["full_text"]
        doc.parsing_status = "success"
        doc.processed_at = datetime.utcnow()
        db.commit()
        db.refresh(doc)
    except Exception as e:
        doc.parsing_status = "failed"
        doc.parsing_error = str(e)
        doc.processed_at = datetime.utcnow()
        db.commit()
        raise HTTPException(status_code=500, detail=f"PDF parsing failed: {str(e)}")

    # --- run NLP analysis ---
    return _run_analysis(doc, framework=framework)


# ---------------------------------------------------------------------------
# Re-analyse an existing document
# ---------------------------------------------------------------------------

@router.post("/{document_id}/analyze", response_model=AnalysisResult)
def analyze_document(
    document_id: int,
    framework: str = Query("gri", description="Framework lens: gri|sasb|tcfd|esrs"),
    db: Session = Depends(get_db),
):
    """
    Run (or re-run) NLP ESG analysis on an already-uploaded document.
    The document must have been successfully parsed first.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")

    return _run_analysis(doc, framework=framework)
