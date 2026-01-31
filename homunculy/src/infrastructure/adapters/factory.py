"""
Adapter Factory - Create adapters based on configuration.

This is the SINGLE POINT where you switch between:
- LangGraph ↔ AutoGen (orchestration)
- LiveKit ↔ Daily (transport)
- OpenAI ↔ ElevenLabs (pipeline)
- Reflex ↔ Cognition (dual-system)
 - LangGraph ↔ AutoGen (orchestration)
 - OpenAI ↔ ElevenLabs (pipeline)
 - Reflex ↔ Cognition (dual-system)

Clean Architecture: Infrastructure wiring happens here, not in domain.
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from common.logger import get_logger

if TYPE_CHECKING:
    from domain.interfaces import (
        CognitionPort,
        DualSystemPort,
        EmotionDetectorPort,
        OrchestratorPort,
        PipelinePort,
        ReflexPort,
        RoomPort,
        SupervisorPort,
        TokenGeneratorPort,
    )

logger = get_logger(__name__)


class OrchestrationFramework(str, Enum):
    """Available orchestration frameworks."""

    LANGGRAPH = "langgraph"
    SWARM = "swarm"
    AUTOGEN = "autogen"  # Future


class TransportProvider(str, Enum):
    """Available transport providers."""

    # Transport providers removed (LiveKit/Pipecat removed from project)


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
    if framework == OrchestrationFramework.SWARM:
        return _swarm_orchestrator(**kwargs)
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


def create_room():
    """Room transport removed from project.

    LiveKit and other transport providers were removed. This factory
    no longer creates room adapters. Callers should not request
    transport-specific adapters anymore.
    """
    raise NotImplementedError("Transport providers removed from project")


def create_token_generator(
    **kwargs,
) -> "TokenGeneratorPort":
    """Token generator removed from project (LiveKit-specific)."""
    raise NotImplementedError("Token generator removed from project")


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
    """Create LangGraph orchestrator.

    For agent use case, wraps the supervisor as orchestrator.
    If a 'graph' kwarg is provided, uses LangGraphOrchestrator directly.
    """
    if "graph" in kwargs:
        from infrastructure.adapters.orchestration import LangGraphOrchestrator

        return LangGraphOrchestrator(**kwargs)

    # Default: use supervisor-based orchestrator for agents
    from infrastructure.adapters.orchestration import (
        LangGraphSupervisorAdapter,
        SupervisorOrchestrator,
        register_all_agents,
    )
    from infrastructure.config import get_settings

    settings = get_settings()
    api_key = kwargs.get("api_key", settings.llm.api_key)
    model = kwargs.get("model", settings.llm.model)

    supervisor = LangGraphSupervisorAdapter(api_key=api_key, model=model)
    register_all_agents(supervisor, api_key, model)
    return SupervisorOrchestrator(supervisor)


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


def _swarm_orchestrator(**kwargs) -> "OrchestratorPort":
    """Create LangGraph Swarm orchestrator."""
    from infrastructure.adapters.orchestration import SwarmOrchestrator
    from infrastructure.config import get_settings

    settings = get_settings()
    api_key = kwargs.get("api_key", settings.llm.api_key)
    model = kwargs.get("model", settings.llm.model)
    return SwarmOrchestrator(api_key=api_key, model=model)


def _livekit_room() -> "RoomPort":
    raise NotImplementedError("LiveKit transport removed from project")


def _livekit_token_generator(**kwargs) -> "TokenGeneratorPort":
    raise NotImplementedError("LiveKit token generator removed from project")


def _openai_pipeline(**kwargs) -> "PipelinePort":
    """Create OpenAI pipeline."""
    from infrastructure.adapters.pipeline import create_openai_pipeline

    return create_openai_pipeline(**kwargs)


# =============================================================================
# Dual-System Factories (2026 Architecture)
# =============================================================================


def create_reflex(**kwargs) -> "ReflexPort":
    """Create reflex adapter for fast responses."""
    from infrastructure.adapters.dual_system import ReflexAdapter

    return ReflexAdapter(**kwargs)


def create_cognition(
    orchestrator: "OrchestratorPort | None" = None,
    **kwargs,
) -> "CognitionPort":
    """Create cognition adapter for deep reasoning."""
    from infrastructure.adapters.dual_system import CognitionAdapter

    if orchestrator is None:
        orchestrator = create_orchestrator()
    return CognitionAdapter(orchestrator=orchestrator, **kwargs)


def create_emotion_detector(**kwargs) -> "EmotionDetectorPort":
    """Create emotion detector."""
    from infrastructure.adapters.dual_system import EmotionDetector

    return EmotionDetector(**kwargs)


def create_dual_system(
    reflex: "ReflexPort | None" = None,
    cognition: "CognitionPort | None" = None,
    emotion: "EmotionDetectorPort | None" = None,
) -> "DualSystemPort":
    """Create dual-system orchestrator.

    This is the main entry point for human-like interaction.
    Combines reflex (fast) + cognition (deep) in parallel.
    """
    from infrastructure.adapters.dual_system import DualSystemOrchestrator

    reflex = reflex or create_reflex()
    cognition = cognition or create_cognition()
    emotion = emotion or create_emotion_detector()
    return DualSystemOrchestrator(reflex, cognition, emotion)
