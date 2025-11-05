"""
SQLAlchemy ORM models for Waifu entities.

These ORM models map domain entities to database tables,
following the Data Mapper pattern.
"""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    Boolean,
    DECIMAL,
    TIMESTAMP,
    ForeignKey,
    ForeignKeyConstraint,
    CheckConstraint,
)
from sqlalchemy.orm import declarative_base, relationship as orm_relationship

Base = declarative_base()


class WaifuORM(Base):
    """ORM model for Waifus table."""
    
    __tablename__ = "waifus"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    
    # JSON fields for embedded objects
    configuration_json = Column(Text, nullable=False)
    appearance_json = Column(Text, nullable=False, default="{}")
    personality_json = Column(Text, nullable=False)
    
    # State
    current_mood = Column(String(50), default="neutral")
    energy_level = Column(DECIMAL(5, 2), default=Decimal("100.00"))
    
    # Metadata
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Statistics
    total_interactions = Column(Integer, default=0)
    total_users = Column(Integer, default=0)
    
    # Relationships
    relationships = orm_relationship("RelationshipORM", back_populates="waifu", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint("energy_level >= 0 AND energy_level <= 100", name="check_energy_level"),
        CheckConstraint("total_interactions >= 0", name="check_total_interactions"),
        CheckConstraint("total_users >= 0", name="check_total_users"),
    )


class RelationshipORM(Base):
    """ORM model for Relationships table."""
    
    __tablename__ = "relationships"
    
    user_id = Column(String(36), primary_key=True)
    waifu_id = Column(String(36), ForeignKey("waifus.id", ondelete="CASCADE"), primary_key=True)
    
    affection_level = Column(DECIMAL(5, 2), default=Decimal("0.00"))
    relationship_stage = Column(String(20), default="stranger")
    interaction_count = Column(Integer, default=0)
    last_interaction = Column(TIMESTAMP(timezone=True), nullable=True)
    
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    special_moments_json = Column(Text, default="[]")
    relationship_notes = Column(Text, default="")
    
    # Relationships
    waifu = orm_relationship("WaifuORM", back_populates="relationships")
    interactions = orm_relationship("InteractionORM", back_populates="relationship", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint("affection_level >= 0 AND affection_level <= 100", name="check_affection_level"),
        CheckConstraint(
            "relationship_stage IN ('stranger', 'acquaintance', 'friend', 'close_friend', 'romantic', 'soulmate')",
            name="check_relationship_stage"
        ),
        CheckConstraint("interaction_count >= 0", name="check_interaction_count"),
    )


class InteractionORM(Base):
    """ORM model for Interactions table."""
    
    __tablename__ = "interactions"
    
    interaction_id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False)
    waifu_id = Column(String(36), nullable=False)
    
    interaction_type = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    affection_change = Column(DECIMAL(5, 2), default=Decimal("0.00"))
    
    user_message = Column(Text, nullable=True)
    waifu_response = Column(Text, nullable=True)
    metadata_json = Column(Text, default="{}")
    
    # Relationships
    relationship = orm_relationship("RelationshipORM", back_populates="interactions")
    
    __table_args__ = (
        ForeignKeyConstraint(
            ["user_id", "waifu_id"],
            ["relationships.user_id", "relationships.waifu_id"],
            ondelete="CASCADE"
        ),
        CheckConstraint(
            "interaction_type IN ('chat', 'gift', 'date', 'compliment', 'activity', 'special_event')",
            name="check_interaction_type"
        ),
    )
