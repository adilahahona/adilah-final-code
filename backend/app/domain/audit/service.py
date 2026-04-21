"""Audit service for logging events."""
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime

from app.models.sql_models import AuditEvent
from app.core.logging import request_id_ctx


class AuditService:
    """
    Service for creating immutable audit events.
    Enforces append-only pattern.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def log_event(
        self,
        event_type: str,
        action: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        user_id: Optional[str] = None,
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None,
        changes: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditEvent:
        """
        Create and persist an audit event.
        
        Args:
            event_type: Type of event (e.g., "ingestion", "mapping", "training")
            action: Action performed (e.g., "create", "update", "approve")
            entity_type: Entity type involved (e.g., "Organization", "Model")
            entity_id: Entity ID if applicable
            user_id: User who performed the action
            before_state: State before action
            after_state: State after action
            changes: Specific changes made
            ip_address: Client IP address
            user_agent: Client user agent
            metadata: Additional context
            
        Returns:
            Created AuditEvent
        """
        # Get request ID from context
        request_id = request_id_ctx.get()
        
        # Create audit event
        event = AuditEvent(
            event_type=event_type,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            before_state=before_state,
            after_state=after_state,
            changes=changes,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata,
            created_at=datetime.utcnow()
        )
        
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        
        return event
    
    def get_events_for_entity(
        self,
        entity_type: str,
        entity_id: int,
        skip: int = 0,
        limit: int = 100
    ):
        """Get all audit events for a specific entity."""
        return (
            self.db.query(AuditEvent)
            .filter(
                AuditEvent.entity_type == entity_type,
                AuditEvent.entity_id == entity_id
            )
            .order_by(AuditEvent.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
