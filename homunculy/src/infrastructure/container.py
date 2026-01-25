"""Dependency Injection Container for Homunculy.

2026 Hybrid Dual-System Architecture:
- ReflexLayer: Fast responses (<300ms)
- CognitionLayer: Deep reasoning (LangGraph)
- DualSystemOrchestrator: Coordinates both

Clean Architecture (SOLID - DIP):
All adapters depend on domain interfaces (ports).
Change provider in config, adapters swap automatically.
"""

from dependency_injector import containers, providers

from infrastructure.adapters.factory import (
    OrchestrationFramework,
    PipelineProvider,
    TransportProvider,
    create_cognition,
    create_dual_system,
    create_emotion_detector,
    create_orchestrator,
    create_pipeline,
    create_reflex,
    create_room,
    create_supervisor,
    create_token_generator,
)
from infrastructure.adapters.langgraph import LangGraphLLMAdapter
from infrastructure.adapters.langgraph.graph_manager import create_graph_manager
from infrastructure.config import get_settings


class Container(containers.DeclarativeContainer):
    """
    Main DI container for Homunculy application.

    Wiring order:
    1. Configuration (settings)
    2. Infrastructure (adapters, persistence)
    3. Dual-System (reflex, cognition, orchestrator)
    4. Transport (LiveKit room, tokens)
    5. Pipeline (STT/LLM/TTS)
    """

    # Configuration
    config = providers.Configuration()
    settings = providers.Singleton(get_settings)

    # --- Framework Selection (change here to switch implementations) ---
    orchestration_framework = providers.Object(OrchestrationFramework.LANGGRAPH)
    transport_provider = providers.Object(TransportProvider.LIVEKIT)
    pipeline_provider = providers.Object(PipelineProvider.OPENAI)

    # --- Orchestration Layer (for Cognition) ---
    orchestrator = providers.Factory(
        create_orchestrator,
        framework=orchestration_framework,
    )
    supervisor = providers.Factory(
        create_supervisor,
        framework=orchestration_framework,
        api_key=providers.Callable(lambda s: s.llm.api_key, settings),
        model=providers.Callable(lambda s: s.llm.model, settings),
        register_agents=True,
    )

    # --- Dual-System Layer (2026 Architecture) ---
    reflex = providers.Factory(create_reflex)
    cognition = providers.Factory(create_cognition, orchestrator=orchestrator)
    emotion_detector = providers.Factory(create_emotion_detector)
    dual_system = providers.Factory(
        create_dual_system,
        reflex=reflex,
        cognition=cognition,
        emotion=emotion_detector,
    )

    # --- Transport Layer (LiveKit → Daily swappable) ---
    room = providers.Factory(create_room, provider=transport_provider)
    token_generator = providers.Factory(
        create_token_generator,
        provider=transport_provider,
    )

    # --- Pipeline Layer (OpenAI → ElevenLabs swappable) ---
    pipeline = providers.Factory(create_pipeline, provider=pipeline_provider)

    # --- LLM Adapter (LangGraph) ---
    # Checkpointer is wired at startup in main.py
    checkpointer = providers.Object(None)
    llm_adapter = providers.Factory(
        lambda api_key, cp: LangGraphLLMAdapter(
            api_key=api_key,
            graph_manager=create_graph_manager(api_key, cp),
        ),
        api_key=providers.Callable(lambda s: s.llm.api_key, settings),
        cp=checkpointer,
    )


# Global container instance
container = Container()


def get_container() -> Container:
    """Get the DI container instance."""
    return container


def get_dual_system():
    """Get dual-system orchestrator from container."""
    return container.dual_system()


def get_orchestrator():
    """Get orchestrator from container."""
    return container.orchestrator()


def get_supervisor():
    """Get supervisor from container."""
    return container.supervisor()


def get_room():
    """Get room adapter from container."""
    return container.room()


def get_token_generator():
    """Get token generator from container."""
    return container.token_generator()


def get_pipeline():
    """Get pipeline from container."""
    return container.pipeline()
