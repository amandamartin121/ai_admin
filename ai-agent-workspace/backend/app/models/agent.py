"""
Agent, AgentRun, AgentStep, and Tool models for agentic AI functionality.
"""

from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    Boolean,
    ForeignKey,
    Index,
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from sqlalchemy import JSON as SAJSON
import enum

from app.models.base import Base, PrimaryKeyMixin, TimestampMixin


class AgentStatus(enum.Enum):
    """Status of an agent run."""

    PENDING = "pending"
    PLANNING = "planning"
    EXECUTING = "executing"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RiskLevel(enum.Enum):
    """Risk level for tools."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Tool(Base, PrimaryKeyMixin, TimestampMixin):
    """
    Tool model representing executable functions for agents.
    
    Tools have schemas, permissions, and risk levels.
    """

    __tablename__ = "tools"

    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=False)
    schema_json = Column(SAJSON, nullable=False)  # JSON Schema for parameters
    permission_required = Column(String(100), nullable=True)  # Permission name
    risk_level = Column(SQLEnum(RiskLevel), default=RiskLevel.LOW, nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)

    # Relationships
    executions = relationship("ToolExecution", back_populates="tool")

    # Indexes
    __table_args__ = (Index("ix_tools_name", "name"),)

    def __repr__(self) -> str:
        return f"<Tool(id={self.id}, name={self.name})>"


class Agent(Base, PrimaryKeyMixin, TimestampMixin):
    """
    Agent model representing configured AI agents.
    
    Agents can have custom instructions, tools, and settings.
    """

    __tablename__ = "agents"

    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    system_prompt = Column(Text, nullable=True)
    is_default = Column(Boolean, default=False, nullable=False)
    allowed_tools = Column(SAJSON, nullable=True)  # List of tool IDs

    # Relationships
    runs = relationship("AgentRun", back_populates="agent")

    def __repr__(self) -> str:
        return f"<Agent(id={self.id}, name={self.name})>"


class AgentRun(Base, PrimaryKeyMixin, TimestampMixin):
    """
    AgentRun model representing a single agent execution session.
    
    Tracks the overall status and progress of agent execution.
    """

    __tablename__ = "agent_runs"

    conversation_id = Column(
        String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    agent_id = Column(PG_UUID(as_uuid=False), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True)
    user_request = Column(Text, nullable=False)
    status = Column(SQLEnum(AgentStatus), default=AgentStatus.PENDING, nullable=False)
    current_step = Column(Integer, default=0, nullable=False)
    total_steps = Column(Integer, nullable=True)
    result = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    metadata_json = Column(SAJSON, nullable=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="agent_runs")
    agent = relationship("Agent", back_populates="runs")
    steps = relationship("AgentStep", back_populates="run", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("ix_agent_runs_conversation_id", "conversation_id"),
        Index("ix_agent_runs_status", "status"),
        Index("ix_agent_runs_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<AgentRun(id={self.id}, status={self.status})>"


class AgentStep(Base, PrimaryKeyMixin, TimestampMixin):
    """
    AgentStep model representing individual steps in agent execution.
    
    Each step represents a thinking, planning, or tool execution action.
    """

    __tablename__ = "agent_steps"

    run_id = Column(
        String(36), ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False
    )
    step_number = Column(Integer, nullable=False)
    step_type = Column(String(50), nullable=False)  # 'thinking', 'tool_call', 'observation', etc.
    description = Column(Text, nullable=False)
    tool_id = Column(PG_UUID(as_uuid=False), ForeignKey("tools.id", ondelete="SET NULL"), nullable=True)
    tool_input = Column(SAJSON, nullable=True)
    tool_output = Column(SAJSON, nullable=True)
    status = Column(String(20), default="pending", nullable=False)
    duration_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)

    # Relationships
    run = relationship("AgentRun", back_populates="steps")
    tool = relationship("Tool")
    execution = relationship(
        "ToolExecution", back_populates="step", uselist=False, cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("ix_agent_steps_run_id", "run_id"),
        Index("ix_agent_steps_step_number", "step_number"),
    )

    def __repr__(self) -> str:
        return f"<AgentStep(id={self.id}, step_type={self.step_type})>"


class ToolExecution(Base, PrimaryKeyMixin, TimestampMixin):
    """
    ToolExecution model tracking individual tool executions.
    
    Records details about tool usage for audit and debugging.
    """

    __tablename__ = "tool_executions"

    step_id = Column(
        String(36), ForeignKey("agent_steps.id", ondelete="CASCADE"), nullable=False
    )
    tool_id = Column(PG_UUID(as_uuid=False), ForeignKey("tools.id", ondelete="CASCADE"), nullable=False)
    input_data = Column(SAJSON, nullable=False)
    output_data = Column(SAJSON, nullable=True)
    status = Column(String(20), default="pending", nullable=False)
    duration_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)

    # Relationships
    step = relationship("AgentStep", back_populates="execution")
    tool = relationship("Tool", back_populates="executions")

    # Indexes
    __table_args__ = (Index("ix_tool_executions_step_id", "step_id"),)

    def __repr__(self) -> str:
        return f"<ToolExecution(id={self.id}, tool_id={self.tool_id})>"
