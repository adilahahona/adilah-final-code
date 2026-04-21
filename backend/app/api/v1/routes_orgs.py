"""
Organization and ReportingPeriod API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.db.repository import OrganizationRepository, ReportingPeriodRepository
from app.models.sql_models import Organization as OrgModel, ReportingPeriod as PeriodModel
from app.models.schemas import (
    Organization, OrganizationCreate, OrganizationUpdate,
    ReportingPeriod, ReportingPeriodCreate
)
from app.models.common import PaginatedResponse


router = APIRouter(prefix="/api/v1/organizations", tags=["Organizations"])


@router.get("", response_model=List[Organization])
async def list_organizations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all organizations with pagination."""
    repo = OrganizationRepository(OrgModel, db)
    orgs = repo.get_all(skip=skip, limit=limit)
    return orgs


@router.post("", response_model=Organization, status_code=status.HTTP_201_CREATED)
async def create_organization(
    org_data: OrganizationCreate,
    db: Session = Depends(get_db)
):
    """Create a new organization."""
    repo = OrganizationRepository(OrgModel, db)
    
    # Check for duplicate name
    existing = repo.get_by_name(org_data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Organization with name '{org_data.name}' already exists"
        )
    
    org = repo.create(**org_data.model_dump())
    return org


@router.get("/{org_id}", response_model=Organization)
async def get_organization(
    org_id: int,
    db: Session = Depends(get_db)
):
    """Get organization by ID."""
    repo = OrganizationRepository(OrgModel, db)
    org = repo.get(org_id)
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization {org_id} not found"
        )
    
    return org


@router.patch("/{org_id}", response_model=Organization)
async def update_organization(
    org_id: int,
    org_data: OrganizationUpdate,
    db: Session = Depends(get_db)
):
    """Update organization."""
    repo = OrganizationRepository(OrgModel, db)
    
    # Only update fields that were provided
    update_data = org_data.model_dump(exclude_unset=True)
    org = repo.update(org_id, **update_data)
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization {org_id} not found"
        )
    
    return org


@router.get("/{org_id}/periods", response_model=List[ReportingPeriod])
async def list_organization_periods(
    org_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all reporting periods for an organization."""
    # Verify organization exists
    org_repo = OrganizationRepository(OrgModel, db)
    org = org_repo.get(org_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization {org_id} not found"
        )
    
    # Get periods
    period_repo = ReportingPeriodRepository(PeriodModel, db)
    periods = period_repo.get_by_organization(org_id, skip=skip, limit=limit)
    return periods


@router.post("/{org_id}/periods", response_model=ReportingPeriod, status_code=status.HTTP_201_CREATED)
async def create_reporting_period(
    org_id: int,
    period_data: ReportingPeriodCreate,
    db: Session = Depends(get_db)
):
    """Create a new reporting period for an organization."""
    # Verify organization exists
    org_repo = OrganizationRepository(OrgModel, db)
    org = org_repo.get(org_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization {org_id} not found"
        )
    
    # Ensure org_id matches
    if period_data.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization ID in path must match organization_id in body"
        )
    
    # Create period
    period_repo = ReportingPeriodRepository(PeriodModel, db)
    period = period_repo.create(**period_data.model_dump())
    return period
