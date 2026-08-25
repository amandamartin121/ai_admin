"""
User model for authentication and authorization.
"""

from sqlalchemy import Column, String, Boolean, DateTime, Index
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import Base, PrimaryKeyMixin, TimestampMixin


class User(Base, PrimaryKeyMixin, TimestampMixin):
    """
    User model representing system users.
    
    Attributes:
        email: Unique email address for login
        username: Display name
        hashed_password: Argon2-hashed password
        is_active: Whether the user can log in
        is_superuser: Whether the user has super admin privileges
        last_login: Last successful login timestamp
    """

    __tablename__ = "users"

    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    files = relationship("File", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="actor", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("ix_users_email", "email", unique=True),
        Index("ix_users_is_active", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"
