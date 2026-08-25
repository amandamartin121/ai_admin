"""
LLMProvider and LLMModel models for AI provider configuration.
"""

from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Index, UniqueConstraint, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

from app.models.base import Base, PrimaryKeyMixin, TimestampMixin


class LLMProvider(Base, PrimaryKeyMixin, TimestampMixin):
    """
    LLMProvider model representing configured AI providers.
    
    Providers can be OpenAI, Anthropic, Ollama, etc.
    """

    __tablename__ = "llm_providers"

    name = Column(String(100), unique=True, nullable=False)
    provider_type = Column(String(50), nullable=False)  # 'openai', 'anthropic', 'ollama', etc.
    base_url = Column(String(500), nullable=False)
    api_key_encrypted = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    config_json = Column(JSONB, nullable=True)

    # Relationships
    models = relationship("LLMModel", back_populates="provider", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (Index("ix_llm_providers_name", "name"),)

    def __repr__(self) -> str:
        return f"<LLMProvider(id={self.id}, name={self.name})>"


class LLMModel(Base, PrimaryKeyMixin, TimestampMixin):
    """
    LLMModel model representing available AI models.
    
    Models are associated with providers and have capabilities metadata.
    """

    __tablename__ = "llm_models"

    provider_id = Column(
        String(36), ForeignKey("llm_providers.id", ondelete="CASCADE"), nullable=False
    )
    model_id = Column(String(100), nullable=False)  # Provider's model ID (e.g., 'gpt-4o')
    display_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    max_tokens = Column(Integer, nullable=True)
    supports_streaming = Column(Boolean, default=True, nullable=False)
    supports_tools = Column(Boolean, default=False, nullable=False)
    supports_vision = Column(Boolean, default=False, nullable=False)
    cost_per_1k_input = Column(Float, nullable=True)
    cost_per_1k_output = Column(Float, nullable=True)
    is_default = Column(Boolean, default=False, nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)
    capabilities_json = Column(JSONB, nullable=True)

    # Relationships
    provider = relationship("LLMProvider", back_populates="models")

    # Indexes
    __table_args__ = (
        Index("ix_llm_models_provider_id", "provider_id"),
        Index("ix_llm_models_model_id", "model_id"),
        UniqueConstraint("provider_id", "model_id", name="uq_provider_model"),
    )

    def __repr__(self) -> str:
        return f"<LLMModel(id={self.id}, model_id={self.model_id})>"
