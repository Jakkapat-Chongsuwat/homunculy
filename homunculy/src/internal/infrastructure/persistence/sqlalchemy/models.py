"""
SQLAlchemy models for Agent entities.

Maps domain entities to database tables.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Float, Integer, JSON
from sqlalchemy.dialects.postgresql import JSONB

from .session import Base


class AgentModel(Base):
    """SQLAlchemy model for Agent entity."""
    
    __tablename__ = "agents"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="idle")
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Configuration stored as JSON
    configuration = Column(JSON, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f"<AgentModel(id={self.id}, name={self.name}, status={self.status})>"
