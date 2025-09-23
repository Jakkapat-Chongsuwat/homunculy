"""
AI Agent Domain Models.

This module defines the domain entities for AI agents, following the Clean Architecture
pattern established in the Pokemon system. These models represent the core business
logic and are independent of any external frameworks.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class AgentProvider(Enum):
    """Supported AI agent providers."""
    
    PYDANTIC_AI = "pydantic_ai"
    OPENAI = "openai"
    LANGRAPH = "langraph"
    AUTOGEN = "autogen"


class AgentStatus(Enum):
    """Agent execution status."""
    
    IDLE = "idle"
    THINKING = "thinking"
    RESPONDING = "responding"
    ERROR = "error"
    COMPLETED = "completed"


@dataclass
class AgentMessage:
    """Represents a message in agent conversation."""
    
    role: str  # user, assistant, system
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


class AgentResponse(BaseModel):
    """Represents an agent's response."""
    
    message: str
    confidence: float
    reasoning: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    status: AgentStatus = AgentStatus.COMPLETED
    

class AgentPersonality(BaseModel):
    """Represents an AI agent's personality traits."""
    
    name: str = Field(..., description="Agent's name")
    description: str = Field(..., description="Agent description")
    traits: Dict[str, float] = Field(
        default_factory=dict,
        description="Personality traits as key-value pairs (0.0-1.0)"
    )
    mood: str = Field(default="neutral", description="Current mood state")
    memory_context: str = Field(default="", description="Long-term memory context")
    

class AgentConfiguration(BaseModel):
    """Configuration for AI agents."""
    
    provider: AgentProvider
    model_name: str
    personality: AgentPersonality
    system_prompt: str = Field(default="", description="System-level instructions")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2000, gt=0)
    tools: List[str] = Field(default_factory=list, description="Available tools/functions")
    

class AgentThread(BaseModel):
    """Represents a conversation thread with an agent."""
    
    id: str
    agent_id: str
    messages: List[AgentMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)