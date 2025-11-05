"""
Waifu Domain Models.

This module defines domain models for the Waifu AI companion feature.
These models extend the base AI agent models with waifu-specific
attributes and behaviors, following Clean Architecture principles.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from .ai_agent import AgentConfiguration, AgentPersonality, AgentProvider


class RelationshipStage(Enum):
    """Stages of relationship progression."""
    
    STRANGER = "stranger"
    ACQUAINTANCE = "acquaintance"
    FRIEND = "friend"
    CLOSE_FRIEND = "close_friend"
    ROMANTIC = "romantic"
    SOULMATE = "soulmate"


class InteractionType(Enum):
    """Types of user-waifu interactions."""
    
    CHAT = "chat"
    GIFT = "gift"
    DATE = "date"
    COMPLIMENT = "compliment"
    ACTIVITY = "activity"
    SPECIAL_EVENT = "special_event"


class WaifuAppearance(BaseModel):
    """Physical appearance attributes of a waifu."""
    
    hair_color: str = Field(default="black", description="Hair color")
    hair_style: str = Field(default="long", description="Hair style")
    eye_color: str = Field(default="brown", description="Eye color")
    height: str = Field(default="average", description="Height description")
    outfit: str = Field(default="casual", description="Current outfit")
    distinguishing_features: List[str] = Field(
        default_factory=list,
        description="Unique physical features"
    )


class WaifuPersonality(AgentPersonality):
    """
    Extended personality model for waifu characters.
    
    Inherits from AgentPersonality and adds waifu-specific traits.
    """
    
    archetype: str = Field(
        default="tsundere",
        description="Personality archetype: tsundere, kuudere, dandere, yandere, etc."
    )
    interests: List[str] = Field(
        default_factory=list,
        description="Hobbies and interests"
    )
    likes: List[str] = Field(
        default_factory=list,
        description="Things the waifu likes"
    )
    dislikes: List[str] = Field(
        default_factory=list,
        description="Things the waifu dislikes"
    )
    background_story: str = Field(
        default="",
        description="Character background and history"
    )
    voice_style: str = Field(
        default="friendly",
        description="Communication style: friendly, formal, playful, shy, etc."
    )


class Interaction(BaseModel):
    """Record of a single interaction with a waifu."""
    
    interaction_id: str = Field(..., description="Unique interaction identifier")
    interaction_type: InteractionType = Field(..., description="Type of interaction")
    content: str = Field(..., description="Interaction content/description")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the interaction occurred"
    )
    affection_change: float = Field(
        default=0.0,
        description="Change in affection level from this interaction"
    )
    user_message: Optional[str] = Field(
        default=None,
        description="User's message if chat interaction"
    )
    waifu_response: Optional[str] = Field(
        default=None,
        description="Waifu's response if chat interaction"
    )
    metadata: Dict[str, str] = Field(
        default_factory=dict,
        description="Additional interaction metadata"
    )


class Relationship(BaseModel):
    """Relationship state between user and waifu."""
    
    user_id: str = Field(..., description="User identifier")
    waifu_id: str = Field(..., description="Waifu identifier")
    affection_level: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Affection level (0-100)"
    )
    relationship_stage: RelationshipStage = Field(
        default=RelationshipStage.STRANGER,
        description="Current relationship stage"
    )
    interaction_count: int = Field(
        default=0,
        ge=0,
        description="Total number of interactions"
    )
    last_interaction: Optional[datetime] = Field(
        default=None,
        description="Timestamp of last interaction"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When relationship was created"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When relationship was last updated"
    )
    interactions_history: List[Interaction] = Field(
        default_factory=list,
        description="Recent interactions (limited to last N)"
    )
    special_moments: List[str] = Field(
        default_factory=list,
        description="Memorable moments in the relationship"
    )
    relationship_notes: str = Field(
        default="",
        description="Notes about the relationship"
    )
    
    def add_interaction(self, interaction: Interaction) -> None:
        """
        Add an interaction and update relationship metrics.
        
        Args:
            interaction: The interaction to add
        """
        self.interactions_history.append(interaction)
        self.interaction_count += 1
        self.affection_level = min(100.0, self.affection_level + interaction.affection_change)
        self.last_interaction = interaction.timestamp
        self.updated_at = datetime.now(timezone.utc)
        
        # Update relationship stage based on affection
        if self.affection_level >= 90:
            self.relationship_stage = RelationshipStage.SOULMATE
        elif self.affection_level >= 75:
            self.relationship_stage = RelationshipStage.ROMANTIC
        elif self.affection_level >= 60:
            self.relationship_stage = RelationshipStage.CLOSE_FRIEND
        elif self.affection_level >= 40:
            self.relationship_stage = RelationshipStage.FRIEND
        elif self.affection_level >= 20:
            self.relationship_stage = RelationshipStage.ACQUAINTANCE
        
        # Keep only recent interactions to prevent unbounded growth
        if len(self.interactions_history) > 100:
            self.interactions_history = self.interactions_history[-100:]


class WaifuConfiguration(AgentConfiguration):
    """
    Configuration for Waifu AI agents.
    
    Extends AgentConfiguration with waifu-specific settings.
    """
    
    # Override personality with WaifuPersonality
    personality: WaifuPersonality = Field(
        ...,
        description="Waifu personality configuration"
    )
    
    # Waifu-specific configuration
    appearance: WaifuAppearance = Field(
        default_factory=WaifuAppearance,
        description="Physical appearance"
    )
    
    enable_relationship_tracking: bool = Field(
        default=True,
        description="Whether to track relationship progression"
    )
    
    enable_memory: bool = Field(
        default=True,
        description="Whether to maintain conversation memory"
    )
    
    max_memory_items: int = Field(
        default=50,
        ge=0,
        description="Maximum number of memory items to retain"
    )
    
    affection_sensitivity: float = Field(
        default=1.0,
        ge=0.0,
        le=2.0,
        description="Multiplier for affection changes (0.5 = less sensitive, 2.0 = more sensitive)"
    )
    
    def __init__(self, **data):
        """Initialize with default provider for waifu agents."""
        if 'provider' not in data:
            data['provider'] = AgentProvider.LANGRAPH
        super().__init__(**data)


class Waifu(BaseModel):
    """
    Complete waifu entity representing an AI companion.
    
    This is the aggregate root for the Waifu domain, combining
    configuration, appearance, personality, and state.
    """
    
    id: str = Field(..., description="Unique waifu identifier")
    name: str = Field(..., description="Waifu name")
    configuration: WaifuConfiguration = Field(..., description="Agent configuration")
    appearance: WaifuAppearance = Field(
        default_factory=WaifuAppearance,
        description="Physical appearance"
    )
    personality: WaifuPersonality = Field(..., description="Personality traits")
    
    # State
    current_mood: str = Field(default="neutral", description="Current emotional state")
    energy_level: float = Field(
        default=100.0,
        ge=0.0,
        le=100.0,
        description="Energy level (affects responsiveness)"
    )
    
    # Metadata
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the waifu was created"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the waifu was last updated"
    )
    is_active: bool = Field(default=True, description="Whether the waifu is active")
    
    # Statistics
    total_interactions: int = Field(
        default=0,
        ge=0,
        description="Total interactions across all users"
    )
    total_users: int = Field(
        default=0,
        ge=0,
        description="Total number of users who have interacted"
    )
    
    def update_mood(self, new_mood: str) -> None:
        """
        Update the waifu's current mood.
        
        Args:
            new_mood: The new mood state
        """
        self.current_mood = new_mood
        self.updated_at = datetime.now(timezone.utc)
    
    def record_interaction(self) -> None:
        """Record that an interaction occurred."""
        self.total_interactions += 1
        self.updated_at = datetime.now(timezone.utc)


class WaifuChatContext(BaseModel):
    """Context for a waifu chat interaction."""
    
    waifu_id: str = Field(..., description="Waifu identifier")
    user_id: str = Field(..., description="User identifier")
    relationship: Optional[Relationship] = Field(
        default=None,
        description="Current relationship state"
    )
    conversation_history: List[str] = Field(
        default_factory=list,
        description="Recent conversation messages"
    )
    user_preferences: Dict[str, str] = Field(
        default_factory=dict,
        description="Known user preferences"
    )
    time_of_day: str = Field(
        default="daytime",
        description="Current time context"
    )
    special_occasion: Optional[str] = Field(
        default=None,
        description="Special occasion if applicable"
    )
