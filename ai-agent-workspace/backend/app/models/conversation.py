"""
Conversation and Message models for chat functionality.
"""

from sqlalchemy import (
    Column,
    String,
    Text,
    Boolean,
    Integer,
    ForeignKey,
    DateTime,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy import JSON as SAJSON

from app.models.base import Base, PrimaryKeyMixin, TimestampMixin


class Conversation(Base, PrimaryKeyMixin, TimestampMixin):
    """
    Conversation model representing a chat session.
    
    Conversations group messages together and can be titled, archived, etc.
    """

    __tablename__ = "conversations"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False, default="New Conversation")
    is_archived = Column(Boolean, default=False, nullable=False)
    mode = Column(String(20), default="chat", nullable=False)  # 'chat' or 'agent'
    model_name = Column(String(100), nullable=True)

    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )
    agent_runs = relationship("AgentRun", back_populates="conversation", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("ix_conversations_user_id", "user_id"),
        Index("ix_conversations_is_archived", "is_archived"),
        Index("ix_conversations_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, title={self.title})>"


class Message(Base, PrimaryKeyMixin, TimestampMixin):
    """
    Message model representing individual chat messages.
    
    Messages belong to conversations and have roles (user/assistant/system).
    """

    __tablename__ = "messages"

    conversation_id = Column(
        String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=True)
    parent_message_id = Column(
        String(36), ForeignKey("messages.id", ondelete="SET NULL"), nullable=True
    )
    metadata_json = Column(SAJSON, nullable=True)  # Additional message metadata

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    attachments = relationship(
        "MessageAttachment", back_populates="message", cascade="all, delete-orphan"
    )
    parent = relationship(
        "Message",
        remote_side="Message.id",
        backref="child_messages",
        foreign_keys=[parent_message_id],
    )

    # Indexes
    __table_args__ = (
        Index("ix_messages_conversation_id", "conversation_id"),
        Index("ix_messages_role", "role"),
        Index("ix_messages_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, role={self.role})>"


class MessageAttachment(Base, PrimaryKeyMixin, TimestampMixin):
    """
    Association table linking messages to files.
    """

    __tablename__ = "message_attachments"

    message_id = Column(
        String(36), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False
    )
    file_id = Column(String(36), ForeignKey("files.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    message = relationship("Message", back_populates="attachments")
    file = relationship("File")

    # Constraints
    __table_args__ = (
        UniqueConstraint("message_id", "file_id", name="uq_message_file"),
        Index("ix_message_attachments_message_id", "message_id"),
        Index("ix_message_attachments_file_id", "file_id"),
    )

    def __repr__(self) -> str:
        return f"<MessageAttachment(message_id={self.message_id}, file_id={self.file_id})>"
