"""Domain interfaces (ports) - Abstract contracts for external services.

Clean Architecture: These are the contracts that domain/application layers use.
Infrastructure adapters implement these - allowing swappable implementations.

Key abstractions:
- CompanionPort: Main AI companion (Yui/Jarvis style)
- MemoryPort: Long-term memory for companion
- PersonaPort: Character/personality management
- OrchestrationPort: LangGraph → AutoGen swappable
- TransportPort: WebRTC or other transports (optional)
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
from domain.interfaces.companion import (
    CompanionContext,
    CompanionInput,
    CompanionOutput,
    CompanionPort,
)
from domain.interfaces.companion import (
    EmotionalTone as CompanionTone,
)
from domain.interfaces.dual_system import (
    CognitionOutput,
    CognitionPort,
    DualSystemInput,
    DualSystemOutput,
    DualSystemPort,
    EmotionalTone,
    EmotionDetectorPort,
    ReflexOutput,
    ReflexPort,
    ResponseType,
)
from domain.interfaces.gateway import (
    ChannelClientPort,
    ChannelInbound,
    ChannelOutbound,
    ChannelTokenProviderPort,
    SessionStorePort,
    TenantPolicyPort,
)
from domain.interfaces.llm import LLMPort
from domain.interfaces.memory import (
    Memory,
    MemoryPort,
    MemoryQuery,
    MemoryResult,
    MemoryType,
)
from domain.interfaces.orchestration import (
    CheckpointerPort,
    OrchestrationConfig,
    OrchestrationInput,
    OrchestrationOutput,
    OrchestratorPort,
    SupervisorPort,
)
from domain.interfaces.persona import (
    PERSONA_JARVIS,
    PERSONA_YUI,
    Persona,
    PersonaPort,
    PersonaTrait,
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
    # Companion (Main AI - Yui/Jarvis style)
    "CompanionContext",
    "CompanionInput",
    "CompanionOutput",
    "CompanionPort",
    "CompanionTone",
    # Memory (Long-term companion memory)
    "Memory",
    "MemoryPort",
    "MemoryQuery",
    "MemoryResult",
    "MemoryType",
    # Persona (Character/personality)
    "Persona",
    "PersonaPort",
    "PersonaTrait",
    "PERSONA_JARVIS",
    "PERSONA_YUI",
    # Dual-System (2026 Hybrid Architecture)
    "CognitionOutput",
    "CognitionPort",
    "DualSystemInput",
    "DualSystemOutput",
    "DualSystemPort",
    "EmotionalTone",
    "EmotionDetectorPort",
    "ReflexOutput",
    "ReflexPort",
    "ResponseType",
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
    # Gateway (channel routing)
    "ChannelClientPort",
    "ChannelInbound",
    "ChannelOutbound",
    "ChannelTokenProviderPort",
    "SessionStorePort",
    "TenantPolicyPort",
    # Pipeline (STT/LLM/TTS abstraction)
    "PipelineConfig",
    "PipelinePort",
    "SpeechToTextPort",
    "SynthesisResult",
    "TextToSpeechPort",
    "TranscriptionResult",
    "VoiceActivityDetectorPort",
    # Service ports
    "LLMPort",
    "RAGPort",
    "STTPort",
    "TTSPort",
]
