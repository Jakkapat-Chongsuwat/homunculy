"""SQLAlchemy models for Agent entities."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, JSON, String

from ..services.session import Base


class AgentModel(Base):
    """SQLAlchemy model for Agent entity."""

    __tablename__ = "agents"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="idle")
    is_active = Column(Boolean, nullable=False, default=True)
    configuration = Column(JSON, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<AgentModel(id={self.id}, name={self.name}, status={self.status})>"
