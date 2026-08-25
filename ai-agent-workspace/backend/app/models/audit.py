"""
AuditLog model for security and compliance logging.
"""

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, String, Text, ForeignKey, Index, DateTime, JSON as SAJSON
from sqlalchemy.orm import relationship

from app.models.base import Base, PrimaryKeyMixin, TimestampMixin


class AuditAction:
    """Constants for audit action types."""

    # Authentication
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILED = "LOGIN_FAILED"
    LOGOUT = "LOGOUT"
    PASSWORD_CHANGED = "PASSWORD_CHANGED"

    # User Management
    USER_CREATED = "USER_CREATED"
    USER_UPDATED = "USER_UPDATED"
    USER_DELETED = "USER_DELETED"
    ROLE_CHANGED = "ROLE_CHANGED"
    PERMISSION_CHANGED = "PERMISSION_CHANGED"

    # Agent Actions
    AGENT_STARTED = "AGENT_STARTED"
    AGENT_COMPLETED = "AGENT_COMPLETED"
    AGENT_FAILED = "AGENT_FAILED"
    TOOL_EXECUTED = "TOOL_EXECUTED"
    TOOL_REJECTED = "TOOL_REJECTED"
    APPROVAL_REQUESTED = "APPROVAL_REQUESTED"
    APPROVAL_APPROVED = "APPROVAL_APPROVED"
    APPROVAL_REJECTED = "APPROVAL_REJECTED"

    # File Operations
    FILE_UPLOADED = "FILE_UPLOADED"
    FILE_DOWNLOADED = "FILE_DOWNLOADED"
    FILE_DELETED = "FILE_DELETED"

    # System
    MODEL_CHANGED = "MODEL_CHANGED"
    SETTINGS_CHANGED = "SETTINGS_CHANGED"


class AuditLog(Base, PrimaryKeyMixin, TimestampMixin):
    """
    AuditLog model for tracking security-relevant events.
    
    Records who did what, when, and with what outcome.
    """

    __tablename__ = "audit_logs"

    actor_user_id = Column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action = Column(String(50), nullable=False, index=True)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(PG_UUID(as_uuid=False), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    status = Column(String(20), default="success", nullable=False)  # success, failure, denied
    metadata_json = Column(SAJSON, nullable=True)

    # Relationships
    actor = relationship("User", back_populates="audit_logs")

    # Indexes
    __table_args__ = (
        Index("ix_audit_logs_actor_user_id", "actor_user_id"),
        Index("ix_audit_logs_action", "action"),
        Index("ix_audit_logs_resource_type", "resource_type"),
        Index("ix_audit_logs_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action={self.action})>"
