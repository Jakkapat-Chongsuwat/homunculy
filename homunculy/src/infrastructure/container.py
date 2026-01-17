"""Dependency Injection Container for Homunculy.

Centralizes all dependency wiring using dependency-injector.
Following Clean Architecture - infrastructure depends on domain interfaces.
"""

from dependency_injector import containers, providers

from infrastructure.config import get_settings


class Container(containers.DeclarativeContainer):
    """
    Main DI container for Homunculy application.

    Wiring order:
    1. Configuration (settings)
    2. Infrastructure (adapters, persistence)
    3. Application (use cases, graph manager)
    4. Presentation (handlers)
    """

    # Configuration
    config = providers.Configuration()
    settings = providers.Singleton(get_settings)

    # Checkpointer (lazy - created at startup)
    checkpointer = providers.Object(None)

    # LLM Adapter (lazy - created at startup)
    llm_adapter = providers.Object(None)

    # TTS Adapter (lazy - created at startup)
    tts_adapter = providers.Object(None)


# Global container instance
container = Container()


def get_container() -> Container:
    """Get the DI container instance."""
    return container
