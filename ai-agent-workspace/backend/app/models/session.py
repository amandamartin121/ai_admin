"""
Session model for tracking user sessions and managing tokens.
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, PrimaryKeyMixin, TimestampMixin


class Session(Base, PrimaryKeyMixin, TimestampMixin):
    """
    Session model representing active user sessions.
    
    Tracks refresh tokens and allows session management/revocation.
    """

    __tablename__ = "sessions"

    user_id = Column(PG_UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    refresh_token_hash = Column(String(255), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(String(500), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="sessions")

    # Indexes
    __table_args__ = (
        Index("ix_sessions_user_id", "user_id"),
        Index("ix_sessions_is_active", "is_active"),
        Index("ix_sessions_expires_at", "expires_at"),
    )

    def __repr__(self) -> str:
        return f"<Session(id={self.id}, user_id={self.user_id})>"
