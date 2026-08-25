"""
Audit logging service for security and compliance.
"""

from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime, timezone


class AuditService:
    """Service for creating and querying audit logs."""

    def __init__(self, db: Session):
        self.db = db

    async def log_action(
        self,
        action: str,
        actor_user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = "success",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> dict:
        """
        Log an action to the audit log.
        
        Args:
            action: The action performed (e.g., 'LOGIN_SUCCESS')
            actor_user_id: ID of the user who performed the action
            resource_type: Type of resource affected (e.g., 'user', 'conversation')
            resource_id: ID of the resource affected
            ip_address: IP address of the request
            user_agent: User agent string
            status: Status of the action ('success', 'failure', 'denied')
            metadata: Additional metadata as a dictionary
            
        Returns:
            The created audit log entry as a dictionary
        """
        from app.models.audit import AuditLog
        
        audit_log = AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            metadata_json=metadata,
        )
        
        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(audit_log)
        
        return {
            "id": audit_log.id,
            "actor_user_id": audit_log.actor_user_id,
            "action": audit_log.action,
            "resource_type": audit_log.resource_type,
            "resource_id": audit_log.resource_id,
            "ip_address": audit_log.ip_address,
            "user_agent": audit_log.user_agent,
            "status": audit_log.status,
            "created_at": audit_log.created_at,
        }

    async def get_audit_logs(
        self,
        limit: int = 100,
        offset: int = 0,
        action: Optional[str] = None,
        actor_user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> tuple[list, int]:
        """
        Query audit logs with filters.
        
        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            action: Filter by action type
            actor_user_id: Filter by actor user ID
            resource_type: Filter by resource type
            status: Filter by status
            
        Returns:
            Tuple of (list of audit logs, total count)
        """
        from app.models.audit import AuditLog
        
        query = self.db.query(AuditLog)
        
        if action:
            query = query.filter(AuditLog.action == action)
        if actor_user_id:
            query = query.filter(AuditLog.actor_user_id == actor_user_id)
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        if status:
            query = query.filter(AuditLog.status == status)
        
        # Get total count
        total = query.count()
        
        # Get paginated results
        logs = (
            query.order_by(AuditLog.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        
        return [
            {
                "id": log.id,
                "actor_user_id": log.actor_user_id,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "status": log.status,
                "metadata_json": log.metadata_json,
                "created_at": log.created_at,
            }
            for log in logs
        ], total

    async def get_recent_logs(self, limit: int = 50) -> list:
        """Get recent audit logs."""
        logs, _ = await self.get_audit_logs(limit=limit)
        return logs
