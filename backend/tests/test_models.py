"""
Unit tests for database models and core functionality.
"""
import pytest
from datetime import datetime

from app.models.sql_models import Organization, ReportingPeriod, Indicator, Framework
from app.models.auth_models import User, UserRole


def test_create_organization(db, sample_org):
    """Test organization creation."""
    assert sample_org.id is not None
    assert sample_org.name == "Test Corporation"
    assert sample_org.external_id == "TEST001"
    assert sample_org.sector == "Technology"
    assert sample_org.country == "USA"


def test_create_reporting_period(db, sample_period, sample_org):
    """Test reporting period creation."""
    assert sample_period.id is not None
    assert sample_period.organization_id == sample_org.id
    assert sample_period.period_type == "annual"


def test_organization_period_relationship(db, sample_org, sample_period):
    """Test relationship between organization and periods."""
    # Refresh to load relationships
    db.refresh(sample_org)
    
    assert len(sample_org.periods) == 1
    assert sample_org.periods[0].id == sample_period.id


def test_create_indicator(db, sample_indicator, sample_framework):
    """Test indicator creation."""
    assert sample_indicator.id is not None
    assert sample_indicator.code == "GRI-305-1"
    assert sample_indicator.pillar == "E"
    assert sample_indicator.framework_id == sample_framework.id


def test_user_password_hashing(db):
    """Test that passwords are properly hashed."""
    password = "securepassword123"
    hashed = User.hash_password(password)
    
    assert hashed != password
    assert len(hashed) > 20  # Bcrypt hashes are long
    
    # Test verification
    user = User(
        username="hashtest",
        email="hash@test.com",
        hashed_password=hashed,
        role=UserRole.VIEWER
    )
    
    assert user.verify_password(password) is True
    assert user.verify_password("wrongpassword") is False


def test_user_permissions(db, sample_user, admin_user):
    """Test user role permissions."""
    # Analyst can read and write
    assert sample_user.can_read() is True
    assert sample_user.can_write() is True
    assert sample_user.can_approve_models() is False
    assert sample_user.can_manage_users() is False
    
    # Admin has all permissions
    assert admin_user.can_read() is True
    assert admin_user.can_write() is True
    assert admin_user.can_approve_models() is True
    assert admin_user.can_manage_users() is True


def test_inactive_user_permissions(db):
    """Test that inactive users have no permissions."""
    user = User(
        username="inactive",
        email="inactive@test.com",
        hashed_password=User.hash_password("password"),
        role=UserRole.ADMIN,
        is_active=False
    )
    
    assert user.can_read() is False
    assert user.can_write() is False
    assert user.can_approve_models() is False


def test_feature_vector_creation(db, sample_feature_vector, sample_org):
    """Test feature vector creation with JSON features."""
    assert sample_feature_vector.id is not None
    assert sample_feature_vector.organization_id == sample_org.id
    assert "ghg_emissions" in sample_feature_vector.features
    assert sample_feature_vector.features["ghg_emissions"] == 1000.0
    assert sample_feature_vector.coverage == 1.0


def test_cascade_delete_organization(db, sample_org, sample_period):
    """Test that deleting an organization cascades to periods."""
    org_id = sample_org.id
    period_id = sample_period.id
    
    # Delete organization
    db.delete(sample_org)
    db.commit()
    
    # Check that organization is deleted
    assert db.query(Organization).filter(Organization.id == org_id).first() is None
    
    # Check that period is also deleted (cascade)
    assert db.query(ReportingPeriod).filter(ReportingPeriod.id == period_id).first() is None
