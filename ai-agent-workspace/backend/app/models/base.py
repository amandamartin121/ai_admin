"""
Base model for all SQLAlchemy models.
Provides common fields and utilities.
"""

from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import declarative_base
import uuid6


def generate_uuid() -> str:
    """Generate a version 6 UUID."""
    return str(uuid6.uuid6())


Base = declarative_base()


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps to models."""

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class PrimaryKeyMixin:
    """Mixin to add UUID primary key to models."""

    id = Column(PG_UUID(as_uuid=False), primary_key=True, default=generate_uuid)
