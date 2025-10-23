from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from common.type import UUIDStr
from common.utils import build_uuid4_str


class Base(DeclarativeBase):
    pass


class AgentConfiguration(Base):
    __tablename__ = "ai_agent_configurations"

    id: Mapped[UUIDStr] = mapped_column(String(32), primary_key=True, default=build_uuid4_str)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    personality_json: Mapped[str] = mapped_column(Text, nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text, default="")
    temperature: Mapped[str] = mapped_column(String(10), default="0.7")
    max_tokens: Mapped[int] = mapped_column(nullable=False, default=2000)
    tools_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class AgentThread(Base):
    __tablename__ = "ai_agent_threads"

    id: Mapped[UUIDStr] = mapped_column(String(32), primary_key=True, default=build_uuid4_str)
    agent_id: Mapped[UUIDStr] = mapped_column(String(32), nullable=False)
    messages_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")


class AgentPersonality(Base):
    __tablename__ = "ai_agent_personalities"

    id: Mapped[UUIDStr] = mapped_column(String(32), primary_key=True, default=build_uuid4_str)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    traits_json: Mapped[str] = mapped_column(Text, default="{}")
    mood: Mapped[str] = mapped_column(String(50), default="neutral")
    memory_context: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))