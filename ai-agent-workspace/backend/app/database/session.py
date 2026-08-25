"""
Database session management and engine configuration.
Supports both PostgreSQL and SQLite.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator
import os

from app.core.config import settings


def get_database_url() -> str:
    """Get the database URL from settings."""
    return settings.database_url


# Create engine based on database type
database_url = get_database_url()

if database_url.startswith("sqlite"):
    # SQLite configuration for development/testing
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
else:
    # PostgreSQL configuration for production
    engine = create_engine(
        database_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session.
    Yields a database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database tables."""
    from app.models.base import Base
    from app.models.user import User
    from app.models.role import Role
    from app.models.permission import Permission
    from app.models.session import Session as SessionModel
    from app.models.conversation import Conversation, Message
    from app.models.file import File
    from app.models.agent import Agent, AgentRun, AgentStep, Tool
    from app.models.audit import AuditLog
    from app.models.approval import ApprovalRequest
    from app.models.llm_provider import LLMProvider, LLMModel
    
    Base.metadata.create_all(bind=engine)
