"""Domain interfaces (ports) - Abstract contracts for external services.

Clean Architecture: These are the contracts that domain/application layers use.
Infrastructure adapters implement these - allowing swappable implementations.

Key abstractions:
- OrchestrationPort: LangGraph → AutoGen swappable
- TransportPort: LiveKit → other WebRTC swappable
- PipelinePort: STT/LLM/TTS pipeline abstraction
"""

from domain.interfaces.agent import (
    AgentContext,
    AgentInput,
    AgentOutput,
    AgentPort,
    AgentRouterPort,
    AgentSessionPort,
)
from domain.interfaces.llm import LLMPort
from domain.interfaces.orchestration import (
    CheckpointerPort,
    OrchestrationConfig,
    OrchestrationInput,
    OrchestrationOutput,
    OrchestratorPort,
    SupervisorPort,
)
from domain.interfaces.pipeline import (
    PipelineConfig,
    PipelinePort,
    SpeechToTextPort,
    SynthesisResult,
    TextToSpeechPort,
    TranscriptionResult,
    VoiceActivityDetectorPort,
)
from domain.interfaces.rag import RAGPort
from domain.interfaces.stt import STTPort
from domain.interfaces.transport import (
    AudioFrame,
    RoomConfig,
    RoomPort,
    SessionConfig,
    TokenGeneratorPort,
    TransportServicePort,
)
from domain.interfaces.tts import TTSPort

__all__ = [
    # Agent
    "AgentContext",
    "AgentInput",
    "AgentOutput",
    "AgentPort",
    "AgentRouterPort",
    "AgentSessionPort",
    # Orchestration (LangGraph/AutoGen abstraction)
    "CheckpointerPort",
    "OrchestrationConfig",
    "OrchestrationInput",
    "OrchestrationOutput",
    "OrchestratorPort",
    "SupervisorPort",
    # Transport (LiveKit/WebRTC abstraction)
    "AudioFrame",
    "RoomConfig",
    "RoomPort",
    "SessionConfig",
    "TokenGeneratorPort",
    "TransportServicePort",
    # Pipeline (STT/LLM/TTS abstraction)
    "PipelineConfig",
    "PipelinePort",
    "SpeechToTextPort",
    "SynthesisResult",
    "TextToSpeechPort",
    "TranscriptionResult",
    "VoiceActivityDetectorPort",
    # Legacy (to be migrated)
    "LLMPort",
    "RAGPort",
    "STTPort",
    "TTSPort",
]
