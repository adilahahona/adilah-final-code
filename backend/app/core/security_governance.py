"""
Model artifact security utilities.
Provides SHA256 checksum verification for model files and immutability checks.
"""
import hashlib
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.event import listens_for
from sqlalchemy import event

from app.models.sql_models import AuditEvent, DatasetSnapshot, ModelVersion


def calculate_file_checksum(file_path: Path) -> str:
    """
    Calculate SHA256 checksum for a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Hex string of the SHA256 checksum
    """
    sha256_hash = hashlib.sha256()
    
    with open(file_path, "rb") as f:
        # Read in chunks for large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    return sha256_hash.hexdigest()


def verify_model_checksum(model: ModelVersion) -> bool:
    """
    Verify that a model's artifact file matches its stored checksum.
    
    Args:
        model: ModelVersion instance with artifact_path and checksum
        
    Returns:
        True if checksum matches, False otherwise
    """
    if not model.artifact_path:
        raise ValueError(f"Model {model.id} has no artifact_path")
    
    if not model.artifact_checksum:
        raise ValueError(f"Model {model.id} has no stored checksum")
    
    file_path = Path(model.artifact_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Model artifact not found: {model.artifact_path}")
    
    actual_checksum = calculate_file_checksum(file_path)
    
    if actual_checksum != model.artifact_checksum:
        raise ValueError(
            f"Checksum mismatch for model {model.id}. "
            f"Expected: {model.artifact_checksum}, Got: {actual_checksum}"
        )
    
    return True


def set_artifact_checksum(model: ModelVersion, file_path: Path) -> str:
    """
    Calculate and set checksum for a model artifact.
    
    Args:
        model: ModelVersion instance
        file_path: Path to the model artifact file
        
    Returns:
        The calculated checksum
    """
    checksum = calculate_file_checksum(file_path)
    model.artifact_path = str(file_path)
    model.artifact_checksum = checksum
    return checksum


# Immutability constraints using SQLAlchemy events

@listens_for(AuditEvent, 'before_update', propagate=True)
def prevent_audit_event_update(mapper, connection, target):
    """Prevent updates to audit events - they should be immutable."""
    raise ValueError("Audit events are immutable and cannot be updated")


@listens_for(AuditEvent, 'before_delete', propagate=True)
def prevent_audit_event_delete(mapper, connection, target):
    """Prevent deletion of audit events - they should be immutable."""
    raise ValueError("Audit events are immutable and cannot be deleted")


@listens_for(DatasetSnapshot, 'before_update', propagate=True)
def prevent_dataset_snapshot_update(mapper, connection, target):
    """Prevent updates to dataset snapshots - they should be immutable."""
    raise ValueError("Dataset snapshots are immutable and cannot be updated")


@listens_for(DatasetSnapshot, 'before_delete', propagate=True)
def prevent_dataset_snapshot_delete(mapper, connection, target):
    """Prevent deletion of dataset snapshots - they should be immutable."""
    raise ValueError("Dataset snapshots are immutable and cannot be deleted")


def enforce_approved_model_only(model: ModelVersion):
    """
    Enforce that only APPROVED models can be used for inference.
    
    Args:
        model: ModelVersion instance
        
    Raises:
        ValueError if model is not approved
    """
    if model.status != "APPROVED":
        raise ValueError(
            f"Model {model.id} ({model.model_name}) has status '{model.status}'. "
            f"Only APPROVED models can be used for inference."
        )


def register_immutability_listeners():
    """
    Register all immutability event listeners.
    Call this during application startup.
    """
    # Event listeners are already registered via @listens_for decorators
    # This function serves as a checkpoint to ensure they're loaded
    pass
