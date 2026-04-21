"""
Tests for security and governance features.
"""
import pytest
from pathlib import Path
import tempfile
import joblib

from app.core.security_governance import (
    calculate_file_checksum,
    verify_model_checksum,
    enforce_approved_model_only
)
from app.models.sql_models import ModelVersion, DatasetSnapshot, AuditEvent
from app.models.auth_models import User, UserRole


def test_checksum_calculation():
    """Test SHA256 checksum calculation."""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False, mode='w') as f:
        f.write("test content for checksum")
        temp_path = Path(f.name)
    
    try:
        checksum = calculate_file_checksum(temp_path)
        
        # Verify checksum format
        assert isinstance(checksum, str)
        assert len(checksum) == 64  # SHA256 produces 64 hex characters
        
        # Verify reproducibility
        checksum2 = calculate_file_checksum(temp_path)
        assert checksum == checksum2
    finally:
        temp_path.unlink()


def test_model_checksum_verification(db, sample_dataset):
    """Test model artifact checksum verification."""
    # Create a temporary model file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.joblib') as f:
        model_data = {"model": "test", "scaler": "test_scaler"}
        joblib.dump(model_data, f.name)
        temp_path = Path(f.name)
    
    try:
        # Calculate checksum
        checksum = calculate_file_checksum(temp_path)
        
        # Create model version with checksum
        model = ModelVersion(
            model_name="checksum_test",
            algorithm="test",
            dataset_snapshot_id=sample_dataset.id,
            artifact_path=str(temp_path),
            artifact_checksum=checksum,
            status="TRAINED"
        )
        db.add(model)
        db.commit()
        db.refresh(model)
        
        # Verify checksum matches
        assert verify_model_checksum(model) is True
        
        # Tamper with checksum
        model.artifact_checksum = "invalid_checksum_12345678" * 2  # Wrong checksum
        
        # Verification should fail
        with pytest.raises(ValueError, match="Checksum mismatch"):
            verify_model_checksum(model)
    finally:
        temp_path.unlink()


def test_enforce_approved_model_only(db, sample_dataset):
    """Test that only APPROVED models can be used for inference."""
    # Create TRAINED model (not approved)
    trained_model = ModelVersion(
        model_name="trained_model",
        algorithm="ridge",
        dataset_snapshot_id=sample_dataset.id,
        status="TRAINED"
    )
    
    # Should raise error for non-approved model
    with pytest.raises(ValueError, match="Only APPROVED models"):
        enforce_approved_model_only(trained_model)
    
    # Create APPROVED model
    approved_model = ModelVersion(
        model_name="approved_model",
        algorithm="ridge",
        dataset_snapshot_id=sample_dataset.id,
        status="APPROVED"
    )
    
    # Should not raise error
    enforce_approved_model_only(approved_model)  # No exception


def test_audit_event_immutability(db):
    """Test that audit events cannot be modified or deleted."""
    from app.models.sql_models import UploadBatch
    
    # Create upload batch first
    batch = UploadBatch(
        data_source_id=1,
        uploaded_by="test",
        status="completed"
    )
    db.add(batch)
    db.commit()
    
    # Create audit event
    event = AuditEvent(
        event_type="test_action",
        entity_type="test_entity",
        entity_id=batch.id,
        user_id="test_user",
        details={"action": "created"}
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    
    # Try to update (should fail)
    event.details = {"action": "modified"}
    with pytest.raises(ValueError, match="immutable"):
        db.commit()
    
    db.rollback()
    
    # Try to delete (should fail)
    with pytest.raises(ValueError, match="immutable"):
        db.delete(event)
        db.commit()


def test_dataset_snapshot_immutability(db, sample_dataset):
    """Test that dataset snapshots cannot be modified or deleted."""
    # Try to update
    sample_dataset.snapshot_name = "modified_name"
    with pytest.raises(ValueError, match="immutable"):
        db.commit()
    
    db.rollback()
    
    # Try to delete
    with pytest.raises(ValueError, match="immutable"):
        db.delete(sample_dataset)
        db.commit()


def test_user_role_hierarchy(db):
    """Test role-based permission hierarchy."""
    viewer = User(
        username="viewer_user",
        email="viewer@test.com",
        hashed_password=User.hash_password("password"),
        role=UserRole.VIEWER,
        is_active=True
    )
    
    analyst = User(
        username="analyst_user",
        email="analyst@test.com",
        hashed_password=User.hash_password("password"),
        role=UserRole.ANALYST,
        is_active=True
    )
    
    admin = User(
        username="admin_user",
        email="admin@test.com",
        hashed_password=User.hash_password("password"),
        role=UserRole.ADMIN,
        is_active=True
    )
    
    # Viewer: can only read
    assert viewer.can_read() is True
    assert viewer.can_write() is False
    assert viewer.can_approve_models() is False
    
    # Analyst: can read and write
    assert analyst.can_read() is True
    assert analyst.can_write() is True
    assert analyst.can_approve_models() is False
    
    # Admin: full permissions
    assert admin.can_read() is True
    assert admin.can_write() is True
    assert admin.can_approve_models() is True


def test_password_security(db):
    """Test password hashing security."""
    password = "secure_password_123!"
    
    user = User(
        username="security_test",
        email="security@test.com",
        hashed_password=User.hash_password(password),
        role=UserRole.VIEWER
    )
    
    # Password should not be stored in plain text
    assert user.hashed_password != password
    
    # Should verify correctly
    assert user.verify_password(password) is True
    
    # Should reject wrong password
    assert user.verify_password("wrong_password") is False
    
    # Hash should be different each time (bcrypt with salt)
    hash1 = User.hash_password(password)
    hash2 = User.hash_password(password)
    assert hash1 != hash2  # Different salts
