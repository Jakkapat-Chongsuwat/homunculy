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
    create_cognition,
    create_dual_system,
    create_emotion_detector,
    create_orchestrator,
    create_pipeline,
    create_reflex,
    create_supervisor,
)
from infrastructure.adapters.gateway.factory import (
    create_channel_client,
    create_gateway_orchestrator,
    create_session_store,
    create_tenant_policy,
    create_token_provider,
)
from infrastructure.adapters.llm import LangGraphLLMAdapter
from infrastructure.adapters.llm.graph_manager import create_graph_manager
from infrastructure.adapters.store import InMemoryStoreAdapter
from infrastructure.config import get_settings


class Container(containers.DeclarativeContainer):
    """Main DI container for Homunculy application."""

    # Configuration
    config = providers.Configuration()
    settings = providers.Singleton(get_settings)

    # --- Framework Selection (change here to switch implementations) ---
    orchestration_framework = providers.Callable(
        lambda s: _resolve_orchestration_framework(s),
        settings,
    )
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

    # --- Pipeline Layer (OpenAI → ElevenLabs swappable) ---
    pipeline = providers.Factory(create_pipeline, provider=pipeline_provider)

    # --- LLM Adapter (LangGraph) ---
    # Checkpointer and Store wired at startup in main.py
    checkpointer = providers.Object(None)
    store = providers.Singleton(InMemoryStoreAdapter)
    llm_adapter = providers.Factory(
        lambda api_key, cp, st: LangGraphLLMAdapter(
            graph_manager=create_graph_manager(_create_llm(api_key), cp, st),
        ),
        api_key=providers.Callable(lambda s: s.llm.api_key, settings),
        cp=checkpointer,
        st=store,
    )

    # --- Gateway (channel router) ---
    session_store = providers.Singleton(create_session_store)
    tenant_policy = providers.Singleton(create_tenant_policy)
    token_provider = providers.Singleton(create_token_provider)
    channel_client = providers.Singleton(create_channel_client)
    gateway_orchestrator = providers.Factory(
        create_gateway_orchestrator,
        dual_system=dual_system,
    )


# Global container instance
container = Container()


def _resolve_orchestration_framework(settings) -> OrchestrationFramework:
    try:
        return OrchestrationFramework(settings.orchestration.framework)
    except ValueError:
        return OrchestrationFramework.LANGGRAPH


def _create_llm(api_key: str):
    """Create LLM instance (vendor-specific, isolated here)."""
    from langchain_openai import ChatOpenAI
    from pydantic import SecretStr

    return ChatOpenAI(api_key=SecretStr(api_key))


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
    raise RuntimeError("Transport removed from container")


def get_token_generator():
    """Get token generator from container."""
    raise RuntimeError("Transport removed from container")


def get_pipeline():
    """Get pipeline from container."""
    return container.pipeline()


def get_store():
    """Get store from container."""
    return container.store()
