"""Dependency Injection Container for Homunculy.

Centralizes all dependency wiring using dependency-injector.
Following Clean Architecture - infrastructure depends on domain interfaces.

Adapter Switching (SOLID - DIP):
- OrchestrationFramework: LANGGRAPH | AUTOGEN
- TransportProvider: LIVEKIT | DAILY
- PipelineProvider: OPENAI | ELEVENLABS

Change provider in config, adapters swap automatically.
"""

from dependency_injector import containers, providers

from infrastructure.adapters.factory import (
    OrchestrationFramework,
    PipelineProvider,
    TransportProvider,
    create_orchestrator,
    create_pipeline,
    create_room,
    create_supervisor,
    create_token_generator,
)
from infrastructure.config import get_settings


class Container(containers.DeclarativeContainer):
    """
    Main DI container for Homunculy application.

    Wiring order:
    1. Configuration (settings)
    2. Infrastructure (adapters, persistence)
    3. Application (use cases, graph manager)
    4. Agents (supervisor, specialists)
    5. Presentation (handlers)
    """

    # Configuration
    config = providers.Configuration()
    settings = providers.Singleton(get_settings)

    # --- Framework Selection (change here to switch implementations) ---
    orchestration_framework = providers.Object(OrchestrationFramework.LANGGRAPH)
    transport_provider = providers.Object(TransportProvider.LIVEKIT)
    pipeline_provider = providers.Object(PipelineProvider.OPENAI)

    # --- Orchestration Layer (LangGraph → AutoGen swappable) ---
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

    # --- Transport Layer (LiveKit → Daily swappable) ---
    room = providers.Factory(
        create_room,
        provider=transport_provider,
    )
    token_generator = providers.Factory(
        create_token_generator,
        provider=transport_provider,
    )

    # --- Pipeline Layer (OpenAI → ElevenLabs swappable) ---
    pipeline = providers.Factory(
        create_pipeline,
        provider=pipeline_provider,
    )

    # --- Legacy (to be migrated) ---
    checkpointer = providers.Object(None)
    llm_adapter = providers.Object(None)
    tts_adapter = providers.Object(None)
    stt_adapter = providers.Object(None)
    agent_router = providers.Object(None)
    session_manager = providers.Object(None)


# Global container instance
container = Container()


def get_container() -> Container:
    """Get the DI container instance."""
    return container


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


# --- Legacy accessors (deprecated) ---


def get_llm():
    """Get LLM adapter from container."""
    return container.llm_adapter()


def get_tts():
    """Get TTS adapter from container."""
    return container.tts_adapter()


def get_stt():
    """Get STT adapter from container."""
    return container.stt_adapter()
