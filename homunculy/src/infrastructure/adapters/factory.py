"""
Adapter Factory - Create adapters based on configuration.

This is the SINGLE POINT where you switch between LangGraph ↔ AutoGen,
LiveKit ↔ other WebRTC, OpenAI ↔ other providers.

Clean Architecture: Infrastructure wiring happens here, not in domain.
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from common.logger import get_logger

if TYPE_CHECKING:
    from domain.interfaces import (
        OrchestratorPort,
        PipelinePort,
        RoomPort,
        SupervisorPort,
        TokenGeneratorPort,
    )

logger = get_logger(__name__)


class OrchestrationFramework(str, Enum):
    """Available orchestration frameworks."""

    LANGGRAPH = "langgraph"
    AUTOGEN = "autogen"  # Future


class TransportProvider(str, Enum):
    """Available transport providers."""

    LIVEKIT = "livekit"
    DAILY = "daily"  # Future


class PipelineProvider(str, Enum):
    """Available pipeline providers."""

    OPENAI = "openai"
    ELEVENLABS = "elevenlabs"  # Future


def create_orchestrator(
    framework: OrchestrationFramework = OrchestrationFramework.LANGGRAPH,
    **kwargs,
) -> "OrchestratorPort":
    """Create orchestrator based on framework."""
    if framework == OrchestrationFramework.LANGGRAPH:
        return _langgraph_orchestrator(**kwargs)
    if framework == OrchestrationFramework.AUTOGEN:
        return _autogen_orchestrator(**kwargs)
    raise ValueError(f"Unknown framework: {framework}")


def create_supervisor(
    framework: OrchestrationFramework = OrchestrationFramework.LANGGRAPH,
    api_key: str = "",
    model: str = "gpt-4o-mini",
    register_agents: bool = True,
    **kwargs,
) -> "SupervisorPort":
    """Create supervisor based on framework.

    Args:
        framework: Which framework to use
        api_key: OpenAI API key
        model: Model name
        register_agents: Whether to register default agents
    """
    if framework == OrchestrationFramework.LANGGRAPH:
        return _langgraph_official_supervisor(api_key, model, register_agents)
    raise ValueError(f"Unknown framework: {framework}")


def create_room(
    provider: TransportProvider = TransportProvider.LIVEKIT,
) -> "RoomPort":
    """Create room adapter based on provider."""
    if provider == TransportProvider.LIVEKIT:
        return _livekit_room()
    raise ValueError(f"Unknown provider: {provider}")


def create_token_generator(
    provider: TransportProvider = TransportProvider.LIVEKIT,
    **kwargs,
) -> "TokenGeneratorPort":
    """Create token generator based on provider."""
    if provider == TransportProvider.LIVEKIT:
        return _livekit_token_generator(**kwargs)
    raise ValueError(f"Unknown provider: {provider}")


def create_pipeline(
    provider: PipelineProvider = PipelineProvider.OPENAI,
    **kwargs,
) -> "PipelinePort":
    """Create pipeline based on provider."""
    if provider == PipelineProvider.OPENAI:
        return _openai_pipeline(**kwargs)
    raise ValueError(f"Unknown provider: {provider}")


# --- Private Factories ---


def _langgraph_orchestrator(**kwargs) -> "OrchestratorPort":
    """Create LangGraph orchestrator."""
    from infrastructure.adapters.orchestration import LangGraphOrchestrator

    return LangGraphOrchestrator(**kwargs)


def _langgraph_supervisor(**kwargs) -> "SupervisorPort":
    """Create basic LangGraph supervisor (legacy)."""
    from infrastructure.adapters.orchestration import LangGraphSupervisor

    return LangGraphSupervisor(**kwargs)


def _langgraph_official_supervisor(
    api_key: str,
    model: str,
    register_agents: bool,
) -> "SupervisorPort":
    """Create official langgraph-supervisor-py supervisor."""
    from infrastructure.adapters.orchestration import (
        LangGraphSupervisorAdapter,
        register_all_agents,
    )

    supervisor = LangGraphSupervisorAdapter(api_key=api_key, model=model)
    if register_agents:
        register_all_agents(supervisor, api_key, model)
    return supervisor


def _autogen_orchestrator(**kwargs) -> "OrchestratorPort":
    """Create AutoGen orchestrator (placeholder)."""
    raise NotImplementedError("AutoGen adapter not yet implemented")


def _livekit_room() -> "RoomPort":
    """Create LiveKit room."""
    from infrastructure.adapters.transport import LiveKitRoom

    return LiveKitRoom()


def _livekit_token_generator(**kwargs) -> "TokenGeneratorPort":
    """Create LiveKit token generator."""
    from infrastructure.adapters.transport import LiveKitTokenGenerator

    return LiveKitTokenGenerator(**kwargs)


def _openai_pipeline(**kwargs) -> "PipelinePort":
    """Create OpenAI pipeline."""
    from infrastructure.adapters.pipeline import create_openai_pipeline

    return create_openai_pipeline(**kwargs)
