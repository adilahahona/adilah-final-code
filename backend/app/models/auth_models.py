"""
User models and RBAC (Role-Based Access Control) for ESG Analytics System.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from passlib.context import CryptContext

from app.db.base import Base, TimestampMixin


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserRole(str, enum.Enum):
    """User roles with different permission levels."""
    VIEWER = "viewer"  # Read-only access
    ANALYST = "analyst"  # Can create manual entries, run inference
    ADMIN = "admin"  # Full access including model approval


class User(Base, TimestampMixin):
    """User accounts with role-based permissions."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    
    # Role and permissions
    role = Column(SQLEnum(UserRole), default=UserRole.VIEWER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    # Audit fields
    last_login_at = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, default=datetime.utcnow)
    
    def verify_password(self, plain_password: str) -> bool:
        """Verify a plain password against the hashed password."""
        return pwd_context.verify(plain_password, self.hashed_password)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a plain password."""
        return pwd_context.hash(password)
    
    def can_read(self) -> bool:
        """All active users can read."""
        return self.is_active
    
    def can_write(self) -> bool:
        """Analysts and admins can write."""
        return self.is_active and self.role in [UserRole.ANALYST, UserRole.ADMIN]
    
    def can_approve_models(self) -> bool:
        """Only admins can approve models."""
        return self.is_active and (self.role == UserRole.ADMIN or self.is_superuser)
    
    def can_manage_users(self) -> bool:
        """Only admins and superusers can manage users."""
        return self.is_active and (self.role == UserRole.ADMIN or self.is_superuser)
