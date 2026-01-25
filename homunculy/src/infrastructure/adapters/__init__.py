"""Infrastructure adapters - External service implementations.

Clean Architecture: Adapters implement domain ports.
Use factory.py to switch between implementations.

Abstraction layers:
- orchestration/: LangGraph → AutoGen swappable
- transport/: LiveKit → Daily swappable
- pipeline/: OpenAI → ElevenLabs swappable
"""

from infrastructure.adapters.elevenlabs import ElevenLabsTTSAdapter
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
from infrastructure.adapters.langgraph import LangGraphLLMAdapter
from infrastructure.adapters.openai import OpenAISTTAdapter
from infrastructure.adapters.orchestration import (
    LangGraphOrchestrator,
    SwarmOrchestrator,
)
from infrastructure.adapters.pipeline import (
    OpenAIPipeline,
    OpenAISTT,
    OpenAITTS,
    SileroVAD,
)
from infrastructure.adapters.transport import (
    LiveKitRoom,
    LiveKitTokenGenerator,
)

__all__ = [
    # Factory (use this to create adapters)
    "OrchestrationFramework",
    "PipelineProvider",
    "TransportProvider",
    "create_orchestrator",
    "create_pipeline",
    "create_room",
    "create_supervisor",
    "create_token_generator",
    # Orchestration adapters
    "LangGraphOrchestrator",
    "SwarmOrchestrator",
    # Transport adapters
    "LiveKitRoom",
    "LiveKitTokenGenerator",
    # Pipeline adapters
    "OpenAIPipeline",
    "OpenAISTT",
    "OpenAITTS",
    "SileroVAD",
    # Service adapters
    "ElevenLabsTTSAdapter",
    "LangGraphLLMAdapter",
    "OpenAISTTAdapter",
]
