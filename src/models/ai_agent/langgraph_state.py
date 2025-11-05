"""
LangGraph State Models.

This module defines Pydantic models for LangGraph state management,
ensuring type-safe state transitions in AI agent workflows.
Following Clean Architecture principles, these models are pure domain
entities with no external dependencies.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ConversationMessage(BaseModel):
    """Single message in a conversation."""
    
    role: str = Field(..., description="Message role: user, assistant, or system")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the message was created"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional message metadata"
    )


class PersonalityContext(BaseModel):
    """Personality context for an AI agent."""
    
    traits: Dict[str, float] = Field(
        default_factory=dict,
        description="Personality traits (0.0-1.0)"
    )
    mood: str = Field(default="neutral", description="Current mood")
    emotional_state: Dict[str, float] = Field(
        default_factory=dict,
        description="Emotional state dimensions"
    )
    memory_summary: str = Field(
        default="",
        description="Summary of relevant memories"
    )


class RelationshipContext(BaseModel):
    """Relationship context between user and AI agent."""
    
    user_id: str = Field(..., description="User identifier")
    agent_id: str = Field(..., description="Agent identifier")
    affection_level: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Affection level (0-100)"
    )
    relationship_stage: str = Field(
        default="stranger",
        description="Relationship stage: stranger, acquaintance, friend, close_friend, romantic"
    )
    interaction_count: int = Field(
        default=0,
        ge=0,
        description="Total interactions"
    )
    last_interaction: Optional[datetime] = Field(
        default=None,
        description="Last interaction timestamp"
    )
    relationship_notes: str = Field(
        default="",
        description="Notes about the relationship"
    )


class ConversationState(BaseModel):
    """
    Core conversation state used by LangGraph.
    
    This model represents the state that flows through
    the LangGraph workflow, enabling type-safe state management.
    """
    
    # Current message being processed
    user_message: str = Field(..., description="Current user message")
    
    # Conversation history
    messages: List[ConversationMessage] = Field(
        default_factory=list,
        description="Conversation history"
    )
    
    # Agent context
    agent_id: str = Field(..., description="Agent identifier")
    agent_name: str = Field(default="AI", description="Agent display name")
    
    # Personality and emotional context
    personality: PersonalityContext = Field(
        default_factory=PersonalityContext,
        description="Current personality state"
    )
    
    # Relationship context (for waifu/companion features)
    relationship: Optional[RelationshipContext] = Field(
        default=None,
        description="Relationship context if applicable"
    )
    
    # Response generation
    response_draft: str = Field(
        default="",
        description="Draft response being constructed"
    )
    response_final: str = Field(
        default="",
        description="Final response to user"
    )
    response_reasoning: str = Field(
        default="",
        description="Reasoning behind the response"
    )
    
    # Workflow control
    current_node: str = Field(
        default="start",
        description="Current node in the workflow"
    )
    next_node: Optional[str] = Field(
        default=None,
        description="Next node to execute"
    )
    
    # Additional context
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context for the conversation"
    )
    
    # Metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Workflow metadata"
    )


class WaifuState(ConversationState):
    """
    Extended state for Waifu/companion AI agents.
    
    Inherits from ConversationState and adds waifu-specific
    fields for managing romantic/companion interactions.
    """
    
    # Waifu-specific attributes
    appearance: Dict[str, str] = Field(
        default_factory=dict,
        description="Physical appearance attributes"
    )
    
    interests: List[str] = Field(
        default_factory=list,
        description="Character interests and hobbies"
    )
    
    background_story: str = Field(
        default="",
        description="Character background and lore"
    )
    
    # Interaction tracking
    gift_received: Optional[str] = Field(
        default=None,
        description="Last gift received from user"
    )
    
    activity_suggestion: Optional[str] = Field(
        default=None,
        description="Suggested activity for interaction"
    )
    
    special_events: List[str] = Field(
        default_factory=list,
        description="Special events/milestones in relationship"
    )


class GraphNodeResult(BaseModel):
    """Result from a LangGraph node execution."""
    
    node_name: str = Field(..., description="Name of the executed node")
    success: bool = Field(default=True, description="Whether execution succeeded")
    output: Dict[str, Any] = Field(
        default_factory=dict,
        description="Node output data"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if execution failed"
    )
    next_node: Optional[str] = Field(
        default=None,
        description="Suggested next node"
    )


class GraphExecutionMetadata(BaseModel):
    """Metadata about graph execution."""
    
    graph_id: str = Field(..., description="Graph identifier")
    execution_id: str = Field(..., description="Execution run identifier")
    start_time: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Execution start time"
    )
    end_time: Optional[datetime] = Field(
        default=None,
        description="Execution end time"
    )
    nodes_executed: List[str] = Field(
        default_factory=list,
        description="List of nodes executed in order"
    )
    total_nodes: int = Field(default=0, ge=0, description="Total nodes in graph")
    status: str = Field(
        default="running",
        description="Execution status: running, completed, failed"
    )
