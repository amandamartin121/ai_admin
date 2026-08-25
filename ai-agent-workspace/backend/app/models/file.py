"""
File model for user-uploaded files.
"""

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, String, Integer, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.models.base import Base, PrimaryKeyMixin, TimestampMixin


class File(Base, PrimaryKeyMixin, TimestampMixin):
    """
    File model representing uploaded files.
    
    Files are owned by users and can be attached to messages.
    """

    __tablename__ = "files"

    user_id = Column(PG_UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)  # in bytes
    file_path = Column(String(500), nullable=False)  # relative path in storage
    checksum = Column(String(64), nullable=True)  # SHA-256 hash
    is_public = Column(Boolean, default=False, nullable=False)

    # Relationships
    user = relationship("User", back_populates="files")

    # Indexes
    __table_args__ = (
        Index("ix_files_user_id", "user_id"),
        Index("ix_files_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<File(id={self.id}, filename={self.filename})>"
