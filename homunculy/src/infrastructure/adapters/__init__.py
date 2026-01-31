"""Infrastructure adapters - External service implementations.

Clean Architecture: Adapters implement domain ports.
Use factory.py to switch between implementations.

Abstraction layers:
- orchestration/: LangGraph → AutoGen swappable
- pipeline/: OpenAI → ElevenLabs swappable
- gateway/: Channel routing adapters
"""

from infrastructure.adapters.elevenlabs import ElevenLabsTTSAdapter
from infrastructure.adapters.factory import (
    OrchestrationFramework,
    PipelineProvider,
    create_orchestrator,
    create_pipeline,
    create_supervisor,
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

__all__ = [
    # Factory (use this to create adapters)
    "OrchestrationFramework",
    "PipelineProvider",
    "create_orchestrator",
    "create_pipeline",
    "create_supervisor",
    # Orchestration adapters
    "LangGraphOrchestrator",
    "SwarmOrchestrator",
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
