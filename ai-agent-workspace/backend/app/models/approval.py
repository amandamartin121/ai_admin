"""
ApprovalRequest model for agent tool approval workflow.
"""

from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Index, Enum as SQLEnum, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy import JSON as SAJSON
import enum

from app.models.base import Base, PrimaryKeyMixin, TimestampMixin


class ApprovalStatus(enum.Enum):
    """Status of an approval request."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ApprovalRequest(Base, PrimaryKeyMixin, TimestampMixin):
    """
    ApprovalRequest model for tracking user approval decisions.
    
    When an agent wants to execute a high-risk tool, an approval
    request is created and the user must explicitly approve or reject.
    """

    __tablename__ = "approval_requests"

    run_id = Column(
        String(36), ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False
    )
    step_id = Column(
        String(36), ForeignKey("agent_steps.id", ondelete="CASCADE"), nullable=True
    )
    tool_id = Column(String(36), ForeignKey("tools.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    action_description = Column(Text, nullable=False)
    risk_level = Column(String(20), nullable=False)
    status = Column(
        SQLEnum(ApprovalStatus), default=ApprovalStatus.PENDING, nullable=False
    )
    approved_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    metadata_json = Column(SAJSON, nullable=True)

    # Relationships
    run = relationship("AgentRun")
    step = relationship("AgentStep")
    tool = relationship("Tool")
    user = relationship("User", foreign_keys=[user_id])
    approver = relationship("User", foreign_keys=[approved_by])

    # Indexes
    __table_args__ = (
        Index("ix_approval_requests_run_id", "run_id"),
        Index("ix_approval_requests_user_id", "user_id"),
        Index("ix_approval_requests_status", "status"),
        Index("ix_approval_requests_expires_at", "expires_at"),
    )

    def __repr__(self) -> str:
        return f"<ApprovalRequest(id={self.id}, status={self.status})>"
