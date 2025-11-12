"""
LangGraph LLM Service Implementation.

Provides LLM orchestration using LangGraph StateGraph with PydanticAI as the model provider.
This follows Clean Architecture by implementing the domain LLMService interface.

LangGraph acts as the orchestrator for conversation flow and state management,
while PydanticAI provides the actual LLM model inference.
"""

import os
from typing import Optional, Dict, Any, Annotated
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from pydantic_ai import Agent as PydanticAgent, ModelSettings
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from internal.domain.services import LLMService
from internal.domain.entities import AgentResponse, AgentConfiguration, AgentStatus


class ConversationState(TypedDict):
    """
    State for LangGraph conversation flow.
    
    Uses add_messages to properly append new messages to the conversation history.
    Following LangGraph best practices for conversational agents.
    """
    messages: Annotated[list, add_messages]
    system_prompt: str
    response: Optional[str]
    error: Optional[str]


class LangGraphLLMService(LLMService):
    """
    LangGraph-based LLM service implementation.
    
    Uses LangGraph as the orchestrator for conversation flow and state management,
    with PydanticAI providing the actual LLM model inference.
    
    This architecture provides:
    - Robust state management via LangGraph
    - Flexible conversation flow control
    - Built-in error handling and retry capabilities
    - Model abstraction through PydanticAI
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize LangGraph LLM service.
        
        Args:
            api_key: OpenAI API key (defaults to LLM_OPENAI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("LLM_OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("OpenAI API key not provided. Set LLM_OPENAI_API_KEY environment variable.")
    
    def _create_pydantic_agent(
        self,
        configuration: AgentConfiguration
    ) -> PydanticAgent:
        """
        Create a PydanticAI agent with proper configuration.
        
        Args:
            configuration: Agent configuration including model, temperature, etc.
            
        Returns:
            Configured PydanticAI agent
        """
        # Create OpenAI provider with API key
        provider = OpenAIProvider(api_key=self.api_key)
        
        # Create OpenAI chat model with provider
        model = OpenAIChatModel(
            configuration.model_name,
            provider=provider
        )
        
        # Build system prompt with personality
        personality = configuration.personality
        personality_context = (
            f"You are {personality.name}. {personality.description}. "
            f"Your current mood is {personality.mood}."
        )
        
        full_system_prompt = f"{configuration.system_prompt}\n\n{personality_context}".strip()
        
        # Create PydanticAI agent
        agent = PydanticAgent(
            model,
            system_prompt=full_system_prompt,
            model_settings=ModelSettings(
                temperature=configuration.temperature,
                max_tokens=configuration.max_tokens
            )
        )
        
        return agent
    
    def _create_llm_node(self, agent: PydanticAgent):
        """
        Create a LangGraph node that calls the PydanticAI agent.
        
        This is a factory function that creates a node function with the agent captured.
        Following LangGraph best practices for node creation.
        
        Args:
            agent: PydanticAI agent to use for inference
            
        Returns:
            Node function compatible with LangGraph
        """
        async def call_llm(state: ConversationState) -> Dict[str, Any]:
            """
            LangGraph node that invokes the PydanticAI agent.
            
            Args:
                state: Current conversation state
                
            Returns:
                State updates with LLM response or error
            """
            try:
                # Get the last user message
                messages = state.get("messages", [])
                if not messages:
                    return {"error": "No messages in conversation"}
                
                # Extract user message content
                last_message = messages[-1]
                if isinstance(last_message, dict):
                    user_input = last_message.get("content", str(last_message))
                else:
                    user_input = str(last_message)
                
                # Call PydanticAI agent
                result = await agent.run(user_input)
                
                # Extract response
                response_text = result.output
                
                # Return state update
                return {
                    "response": response_text,
                    "messages": [{"role": "assistant", "content": response_text}],
                    "error": None
                }
                
            except Exception as e:
                return {
                    "error": str(e),
                    "response": None
                }
        
        return call_llm
    
    def _build_conversation_graph(self, agent: PydanticAgent):
        """
        Build the LangGraph StateGraph for conversation flow.
        
        Following LangGraph best practices:
        - Clear state definition using TypedDict
        - Simple linear flow for basic conversation
        - Error handling built into nodes
        
        Args:
            agent: PydanticAI agent to use in the graph
            
        Returns:
            Compiled graph ready for execution (CompiledStateGraph)
        """
        # Create graph builder with ConversationState
        graph_builder = StateGraph(ConversationState)
        
        # Add the LLM node
        graph_builder.add_node("llm", self._create_llm_node(agent))
        
        # Define flow: START -> llm -> END
        graph_builder.add_edge(START, "llm")
        graph_builder.add_edge("llm", END)
        
        # Compile the graph
        return graph_builder.compile()
    
    async def chat(
        self,
        configuration: AgentConfiguration,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Send a chat message using LangGraph orchestration with PydanticAI.
        
        Args:
            configuration: Agent configuration with model, temperature, etc.
            message: User message
            context: Optional conversation context
            
        Returns:
            AgentResponse with the LLM's reply
        """
        try:
            # Create PydanticAI agent
            agent = self._create_pydantic_agent(configuration)
            
            # Build LangGraph conversation flow
            graph = self._build_conversation_graph(agent)
            
            # Prepare initial state (as ConversationState)
            initial_state: ConversationState = {
                "messages": [{"role": "user", "content": message}],
                "system_prompt": configuration.system_prompt,
                "response": None,
                "error": None
            }
            
            # Execute the graph
            result = await graph.ainvoke(initial_state)
            
            # Check for errors
            if result.get("error"):
                return AgentResponse(
                    message=f"Error: {result['error']}",
                    confidence=0.0,
                    reasoning="LangGraph execution error",
                    metadata={"error": result["error"]},
                    status=AgentStatus.ERROR
                )
            
            # Extract response
            response_text = result.get("response", "No response generated")
            
            return AgentResponse(
                message=response_text,
                confidence=0.95,
                reasoning=f"Generated by {configuration.model_name} via LangGraph orchestration with PydanticAI",
                metadata={
                    "model": configuration.model_name,
                    "temperature": configuration.temperature,
                    "max_tokens": configuration.max_tokens,
                    "orchestrator": "langgraph",
                    "provider": "pydantic_ai"
                },
                status=AgentStatus.COMPLETED
            )
            
        except Exception as e:
            return AgentResponse(
                message=f"Error: {str(e)}",
                confidence=0.0,
                reasoning="Failed to communicate with LLM via LangGraph",
                metadata={"error": str(e)},
                status=AgentStatus.ERROR
            )
