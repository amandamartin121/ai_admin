"""
Database models initialization.

Import all models here to ensure they are registered with SQLAlchemy
before the database tables are created.
"""

from app.models.base import Base
from app.models.user import User
from app.models.session import Session
from app.models.role import Role, Permission, UserRole, RolePermission
from app.models.conversation import Conversation, Message, MessageAttachment
from app.models.file import File
from app.models.agent import Agent, AgentRun, AgentStep, Tool, ToolExecution
from app.models.approval import ApprovalRequest, ApprovalStatus
from app.models.audit import AuditLog, AuditAction
from app.models.llm_provider import LLMProvider, LLMModel

__all__ = [
    "Base",
    "User",
    "Session",
    "Role",
    "Permission",
    "UserRole",
    "RolePermission",
    "Conversation",
    "Message",
    "MessageAttachment",
    "File",
    "Agent",
    "AgentRun",
    "AgentStep",
    "Tool",
    "ToolExecution",
    "ApprovalRequest",
    "ApprovalStatus",
    "AuditLog",
    "AuditAction",
    "LLMProvider",
    "LLMModel",
]