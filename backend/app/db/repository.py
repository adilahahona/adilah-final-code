"""
Repository pattern helpers for CRUD operations.
"""
from typing import Generic, TypeVar, Type, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.base import Base


ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository with common CRUD operations."""
    
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db
    
    def get(self, id: int) -> Optional[ModelType]:
        """Get single record by ID."""
        return self.db.query(self.model).filter(self.model.id == id).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Get all records with pagination."""
        return self.db.query(self.model).offset(skip).limit(limit).all()
    
    def create(self, **kwargs) -> ModelType:
        """Create new record."""
        instance = self.model(**kwargs)
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance
    
    def update(self, id: int, **kwargs) -> Optional[ModelType]:
        """Update existing record."""
        instance = self.get(id)
        if not instance:
            return None
        
        for key, value in kwargs.items():
            setattr(instance, key, value)
        
        self.db.commit()
        self.db.refresh(instance)
        return instance
    
    def delete(self, id: int) -> bool:
        """Delete record."""
        instance = self.get(id)
        if not instance:
            return False
        
        self.db.delete(instance)
        self.db.commit()
        return True
    
    def count(self) -> int:
        """Count total records."""
        return self.db.query(self.model).count()


class OrganizationRepository(BaseRepository):
    """Repository for Organization model."""
    
    def get_by_name(self, name: str) -> Optional[ModelType]:
        """Get organization by name."""
        return self.db.query(self.model).filter(self.model.name == name).first()
    
    def get_by_external_id(self, external_id: str) -> Optional[ModelType]:
        """Get organization by external ID."""
        return self.db.query(self.model).filter(self.model.external_id == external_id).first()


class ReportingPeriodRepository(BaseRepository):
    """Repository for ReportingPeriod model."""
    
    def get_by_organization(self, org_id: int, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Get all periods for an organization."""
        return (
            self.db.query(self.model)
            .filter(self.model.organization_id == org_id)
            .order_by(desc(self.model.period_start))
            .offset(skip)
            .limit(limit)
            .all()
        )
