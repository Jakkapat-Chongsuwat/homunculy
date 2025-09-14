"""
Repository layer for PydanticAI integration.

This module contains the concrete implementations of LLM operations
using PydanticAI, following the Dependency Inversion principle.
"""

from typing import Any, Dict, Optional
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel

from models.ai_agent.ai_agent import AgentConfiguration, AgentProvider, AgentResponse
from ..llm_service.interfaces import ILLMClient
from settings import PYDANTIC_AI_API_KEY, OPENAI_API_KEY


class PydanticAILLMClient(ILLMClient):
    """Concrete implementation of LLM client using PydanticAI."""

    def __init__(self):
        self._agents: Dict[str, Agent] = {}
        self._agent_configs: Dict[str, AgentConfiguration] = {}

    def _get_api_key(self, provider: AgentProvider) -> str:
        """Get API key for the specified provider."""
        key_mapping = {
            AgentProvider.PYDANTIC_AI: PYDANTIC_AI_API_KEY,
            AgentProvider.OPENAI: OPENAI_API_KEY,
        }

        api_key = key_mapping.get(provider, "")
        if not api_key:
            raise ValueError(f"API key not configured for provider: {provider}")

        return api_key

    def _create_pydantic_ai_agent(self, config: AgentConfiguration) -> Agent:
        """Create a PydanticAI agent."""
        api_key = self._get_api_key(config.provider)

        # Create OpenAI provider with API key
        from pydantic_ai.providers.openai import OpenAIProvider
        provider = OpenAIProvider(api_key=api_key)

        # Create OpenAI model for PydanticAI
        model_name = getattr(config, 'model_name', 'gpt-4')
        model = OpenAIChatModel(model_name, provider=provider)  # type: ignore

        # Create agent with personality and system prompt
        personality = getattr(config, 'personality', None)
        system_prompt = f"""
        {getattr(config, 'system_prompt', '')}

        Your personality: {getattr(personality, 'description', 'AI Assistant') if personality else 'AI Assistant'}
        Current mood: {getattr(personality, 'mood', 'neutral') if personality else 'neutral'}
        Key traits: {', '.join(f"{k}: {v}" for k, v in getattr(personality, 'traits', {}).items()) if personality else ''}
        """

        agent = Agent(
            model=model,
            system_prompt=system_prompt,
        )

        return agent

    def _create_openai_agent(self, config: AgentConfiguration) -> Agent:
        """Create an OpenAI agent."""
        api_key = self._get_api_key(config.provider)

        # Create OpenAI provider with API key
        from pydantic_ai.providers.openai import OpenAIProvider
        provider = OpenAIProvider(api_key=api_key)

        # Create OpenAI model with the provider
        model = OpenAIChatModel(
            config.model_name,  # type: ignore
            provider=provider,
        )

        system_prompt = f"""
        {config.system_prompt or ''}

        Your personality: {getattr(config.personality, 'description', 'AI Assistant')}
        Current mood: {getattr(config.personality, 'mood', 'neutral')}
        Key traits: {', '.join(f"{k}: {v}" for k, v in getattr(config.personality, 'traits', {}).items())}
        """

        agent = Agent(
            model=model,
            system_prompt=system_prompt,
        )

        return agent

    async def create_agent(self, config: AgentConfiguration) -> str:
        """Create an LLM agent and return its ID."""
        import uuid
        agent_id = str(uuid.uuid4())

        if config.provider not in [AgentProvider.PYDANTIC_AI, AgentProvider.OPENAI]:
            raise ValueError(f"Unsupported provider: {config.provider}")

        try:
            if config.provider == AgentProvider.PYDANTIC_AI:
                agent = self._create_pydantic_ai_agent(config)
            else:  # OPENAI
                agent = self._create_openai_agent(config)

            self._agents[agent_id] = agent
            self._agent_configs[agent_id] = config
            return agent_id
        except Exception as e:
            raise RuntimeError(f"Failed to create agent: {str(e)}")

    async def chat(
        self,
        agent_id: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """Send a message to an LLM agent and get response."""
        if agent_id not in self._agents:
            raise ValueError(f"Agent {agent_id} not found")

        agent = self._agents[agent_id]
        config = self._agent_configs[agent_id]

        try:
            # Add context to the message if provided
            full_message = message
            if context:
                context_str = "\n".join(f"{k}: {v}" for k, v in context.items())
                full_message = f"{message}\n\nContext:\n{context_str}"

            # Run the agent
            result = await agent.run(full_message)

            # Get response data safely
            response_data = "I apologize, but I couldn't generate a response at this time."
            if result is None:
                # Handle None result case
                pass  # Keep default message
            else:
                try:
                    # Try to get data using getattr to avoid type checker issues
                    data = getattr(result, 'data', None)
                    if data is not None:
                        response_data = str(data)
                    else:
                        # Try other common attributes
                        output = getattr(result, 'output', None)
                        if output is not None:
                            response_data = str(output)
                        else:
                            response = getattr(result, 'response', None)
                            if response is not None:
                                response_data = str(response)
                            else:
                                # Try to convert result directly to string
                                response_data = str(result)
                except (AttributeError, TypeError, ValueError):
                    response_data = "I apologize, but I couldn't generate a response at this time."

            # Get model info safely
            model_info = "unknown"
            try:
                if hasattr(agent, 'model') and agent.model:
                    model = agent.model
                    # Try different ways to get model name
                    try:
                        if hasattr(model, 'model_name'):
                            model_name_val = getattr(model, 'model_name', None)
                            if model_name_val is not None:
                                model_info = str(model_name_val)
                        elif hasattr(model, 'name'):
                            name_val = getattr(model, 'name', None)
                            if name_val is not None:
                                model_info = str(name_val)
                        elif hasattr(model, '_model_name'):
                            private_name_val = getattr(model, '_model_name', None)
                            if private_name_val is not None:
                                model_info = str(private_name_val)
                    except (AttributeError, TypeError):
                        # If we can't access the attribute safely, use a generic name
                        model_info = "llm-model"
            except (AttributeError, TypeError):
                model_info = "unknown"

            return AgentResponse(
                message=response_data,
                confidence=0.9,  # PydanticAI doesn't provide confidence scores
                reasoning="Response generated by LLM",
                metadata={
                    "agent_id": agent_id,
                    "provider": str(AgentProvider.PYDANTIC_AI if config.provider == AgentProvider.PYDANTIC_AI else AgentProvider.OPENAI),
                    "model": model_info,
                    "status": "llm_response",
                    "usage": getattr(result, 'usage', None) if result else None,
                }
            )

        except Exception as e:
            raise RuntimeError(f"LLM chat failed: {str(e)}")

    async def update_agent(self, agent_id: str, config: AgentConfiguration) -> None:
        """Update an existing agent's configuration."""
        if agent_id in self._agents:
            del self._agents[agent_id]
            del self._agent_configs[agent_id]

        # Create new agent with updated config
        await self.create_agent_with_id(agent_id, config)

    async def create_agent_with_id(self, agent_id: str, config: AgentConfiguration) -> None:
        """Create an agent with a specific ID (used internally for updates)."""
        if config.provider not in [AgentProvider.PYDANTIC_AI, AgentProvider.OPENAI]:
            raise ValueError(f"Unsupported provider: {config.provider}")

        try:
            if config.provider == AgentProvider.PYDANTIC_AI:
                agent = self._create_pydantic_ai_agent(config)
            else:  # OPENAI
                agent = self._create_openai_agent(config)

            self._agents[agent_id] = agent
        except Exception as e:
            raise RuntimeError(f"Failed to create agent: {str(e)}")

    async def remove_agent(self, agent_id: str) -> None:
        """Remove an agent."""
        if agent_id in self._agents:
            del self._agents[agent_id]

    def is_provider_supported(self, provider: str) -> bool:
        """Check if a provider is supported."""
        return provider in ["pydantic_ai", "openai"]