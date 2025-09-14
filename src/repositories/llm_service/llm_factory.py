"""
LLM Factory for creating LLM clients following Dependency Inversion.

This factory creates the appropriate LLM client based on the provider,
decoupling the service layer from concrete implementations.
"""

from typing import Dict
from .interfaces import ILLMClient, ILLMFactory
from ..pydantic_ai_client.pydantic_ai_client import PydanticAILLMClient


class LLMFactory(ILLMFactory):
    """Factory for creating LLM clients."""

    def __init__(self):
        self._clients: Dict[str, ILLMClient] = {}

    def create_client(self, provider: str) -> ILLMClient:
        """Create an LLM client for the specified provider."""
        if provider not in self._clients:
            if provider in ["pydantic_ai", "openai"]:
                self._clients[provider] = PydanticAILLMClient()
            else:
                raise ValueError(f"Unsupported provider: {provider}")

        return self._clients[provider]

    def get_supported_providers(self) -> list[str]:
        """Get list of supported providers."""
        return ["pydantic_ai", "openai"]