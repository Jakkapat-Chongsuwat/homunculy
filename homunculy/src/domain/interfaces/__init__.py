"""Domain interfaces (ports) - Abstract contracts for external services."""

from domain.interfaces.llm import LLMPort
from domain.interfaces.rag import RAGPort
from domain.interfaces.stt import STTPort
from domain.interfaces.tts import TTSPort

__all__ = [
    "LLMPort",
    "RAGPort",
    "STTPort",
    "TTSPort",
]
