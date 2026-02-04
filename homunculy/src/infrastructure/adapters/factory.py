"""
Adapter Factory - Create adapters based on configuration.

This is the SINGLE POINT where you switch between:
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
        SupervisorPort,
    )

logger = get_logger(__name__)


class OrchestrationFramework(str, Enum):
    """Available orchestration frameworks."""

    LANGGRAPH = "langgraph"
    SUPERVISOR = "supervisor"
    SWARM = "swarm"
    AUTOGEN = "autogen"  # Future


class PipelineProvider(str, Enum):
    """Available pipeline providers."""

    OPENAI = "openai"
    ELEVENLABS = "elevenlabs"  # Future


def create_orchestrator(
    framework: OrchestrationFramework = OrchestrationFramework.LANGGRAPH,
    **kwargs,
) -> "OrchestratorPort":
    """Create orchestrator based on framework."""
    if framework == OrchestrationFramework.SUPERVISOR:
        return _langgraph_supervisor_orchestrator(**kwargs)
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

    If a 'graph' kwarg is provided, uses LangGraphOrchestrator directly.
    Otherwise defaults to the supervisor-based orchestrator.
    """
    if "graph" in kwargs:
        from infrastructure.adapters.orchestration import LangGraphOrchestrator

        return LangGraphOrchestrator(**kwargs)

    return _langgraph_supervisor_orchestrator(**kwargs)


def _langgraph_supervisor_orchestrator(**kwargs) -> "OrchestratorPort":
    """Create LangGraph supervisor-based orchestrator."""
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
