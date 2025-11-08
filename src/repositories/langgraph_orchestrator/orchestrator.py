"""
LangGraph Orchestrator LLM Client.

This module implements ILLMClient using LangGraph for workflow orchestration
while using Pydantic AI agents as the execution nodes. This creates a powerful
combination where LangGraph handles the control flow and state management,
while Pydantic AI provides type-safe LLM interactions.

Following Clean Architecture:
- Implements repository interface (ILLMClient)
- Uses domain models (ConversationState, WaifuState)
- Maintains independence from external frameworks at the domain level
"""

from typing import Dict, Any, Optional, AsyncIterator
from uuid import uuid4

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from models.ai_agent.ai_agent import AgentConfiguration, AgentResponse, AgentStatus
from models.ai_agent.langgraph_state import ConversationState, WaifuState, ConversationMessage
from repositories.abstraction.llm import ILLMClient
from repositories.pydantic_ai_client.pydantic_ai_client import PydanticAILLMClient
from .nodes import LangGraphNodeFunctions, should_update_relationship


class LangGraphOrchestratorClient(ILLMClient):
    """
    LangGraph-based LLM client that orchestrates Pydantic AI agents.
    
    This client creates a LangGraph workflow where each node uses a
    Pydantic AI agent for LLM operations. The graph manages state
    transitions and control flow, while Pydantic AI ensures type-safe
    interactions with LLMs.
    
    Architecture:
        LangGraph (Orchestration Layer)
            ├── State Management (ConversationState/WaifuState)
            ├── Workflow Control (Nodes & Edges)
            └── Nodes (Functions)
                └── Pydantic AI Agents (Execution Layer)
    """
    
    def __init__(self):
        """Initialize the LangGraph orchestrator."""
        self._pydantic_client = PydanticAILLMClient()
        self._node_functions = LangGraphNodeFunctions(self._pydantic_client)
        self._graphs: Dict[str, Any] = {}  # Store compiled graphs
        self._agent_configs: Dict[str, AgentConfiguration] = {}
        self._checkpointer = MemorySaver()
    
    def _create_conversation_graph(
        self,
        agent_id: str,
        is_waifu: bool = False
    ) -> StateGraph:
        """
        Create a LangGraph workflow for conversation.
        
        The graph structure:
        START -> personality_analysis -> memory_retrieval -> response_generation 
        -> [relationship_update (if waifu)] -> finalization -> END
        
        Args:
            agent_id: Agent identifier
            is_waifu: Whether this is a waifu agent with relationship tracking
            
        Returns:
            Configured StateGraph
        """
        # Choose state model based on agent type
        state_class = WaifuState if is_waifu else ConversationState
        
        # Create the graph with appropriate state schema
        graph = StateGraph(state_class)
        
        # Add nodes
        graph.add_node(
            "personality_analysis",
            self._node_functions.personality_analysis_node
        )
        graph.add_node(
            "memory_retrieval",
            self._node_functions.memory_retrieval_node
        )
        graph.add_node(
            "response_generation",
            self._node_functions.response_generation_node
        )
        graph.add_node(
            "finalization",
            self._node_functions.response_finalization_node
        )
        
        # Add relationship node for waifu agents
        if is_waifu:
            graph.add_node(
                "relationship_update",
                self._node_functions.relationship_update_node
            )
        
        # Define edges (workflow)
        graph.add_edge(START, "personality_analysis")
        graph.add_edge("personality_analysis", "memory_retrieval")
        graph.add_edge("memory_retrieval", "response_generation")
        
        # Conditional edge: update relationship if waifu, else go to finalization
        if is_waifu:
            graph.add_conditional_edges(
                "response_generation",
                should_update_relationship,
                {
                    "relationship_update": "relationship_update",
                    "finalization": "finalization"
                }
            )
            graph.add_edge("relationship_update", "finalization")
        else:
            graph.add_edge("response_generation", "finalization")
        
        graph.add_edge("finalization", END)
        
        return graph
    
    def create_agent(self, agent_id: str, config: AgentConfiguration) -> None:
        """
        Create an LLM agent with LangGraph orchestration.
        
        This creates:
        1. The main Pydantic AI agent for response generation
        2. A LangGraph workflow that orchestrates multiple specialized agents
        
        Args:
            agent_id: Unique identifier for the agent
            config: Agent configuration
        """
        # Store configuration
        self._agent_configs[agent_id] = config
        
        # Create the main Pydantic AI agent
        # Override provider to PYDANTIC_AI since LangGraph delegates to Pydantic AI for execution
        from models.ai_agent.ai_agent import AgentProvider
        from copy import copy
        pydantic_config = copy(config)
        pydantic_config.provider = AgentProvider.PYDANTIC_AI
        self._pydantic_client.create_agent(agent_id, pydantic_config)
        
        # Determine if this is a waifu agent based on personality or config
        is_waifu = (
            hasattr(config, 'personality') and 
            'waifu' in getattr(config.personality, 'name', '').lower()
        )
        
        # Create the LangGraph workflow
        graph = self._create_conversation_graph(agent_id, is_waifu=is_waifu)
        
        # Compile the graph
        self._graphs[agent_id] = graph.compile(checkpointer=self._checkpointer)
    
    async def chat(
        self,
        agent_id: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Send a message to an agent using LangGraph orchestration.
        
        The message flows through the entire LangGraph workflow:
        personality analysis -> memory retrieval -> response generation
        -> [relationship update] -> finalization
        
        Args:
            agent_id: Agent identifier
            message: User message
            context: Additional context
            
        Returns:
            Agent response with full workflow metadata
        """
        if agent_id not in self._graphs:
            raise ValueError(f"Agent {agent_id} not found")
        
        graph = self._graphs[agent_id]
        config_obj = self._agent_configs.get(agent_id)
        
        # Determine if this is a waifu agent
        is_waifu = (
            config_obj and
            hasattr(config_obj, 'personality') and 
            'waifu' in getattr(config_obj.personality, 'name', '').lower()
        )
        
        # Prepare initial state
        if is_waifu:
            from models.ai_agent.langgraph_state import PersonalityContext, RelationshipContext
            
            initial_state = WaifuState(
                agent_id=agent_id,
                agent_name=getattr(config_obj.personality, 'name', 'Waifu') if config_obj else 'Waifu',
                user_message=message,
                messages=[],
                personality=PersonalityContext(
                    traits=getattr(config_obj.personality, 'traits', {}) if config_obj else {},
                    mood=getattr(config_obj.personality, 'mood', 'neutral') if config_obj else 'neutral'
                ),
                relationship=RelationshipContext(
                    user_id=context.get('user_id', 'default_user') if context else 'default_user',
                    agent_id=agent_id,
                    affection_level=context.get('affection_level', 50.0) if context else 50.0,
                    relationship_stage=context.get('relationship_stage', 'friend') if context else 'friend'
                ),
                context=context or {}
            )
        else:
            from models.ai_agent.langgraph_state import PersonalityContext
            
            initial_state = ConversationState(
                agent_id=agent_id,
                agent_name=getattr(config_obj.personality, 'name', 'AI') if config_obj else 'AI',
                user_message=message,
                messages=[],
                personality=PersonalityContext(
                    traits=getattr(config_obj.personality, 'traits', {}) if config_obj else {},
                    mood=getattr(config_obj.personality, 'mood', 'neutral') if config_obj else 'neutral'
                ),
                context=context or {}
            )
        
        try:
            # Run the graph workflow
            thread_id = context.get('thread_id', str(uuid4())) if context else str(uuid4())
            config_dict = {
                "configurable": {"thread_id": thread_id}
            }
            
            # Execute the workflow
            final_state = await graph.ainvoke(
                initial_state.model_dump(),
                config=config_dict
            )
            
            # Extract response from final state
            response_message = final_state.get("response_final", "")
            response_reasoning = final_state.get("response_reasoning", "")
            
            # Build metadata
            metadata = {
                "agent_id": agent_id,
                "provider": "langgraph",
                "workflow_executed": True,
                "nodes_executed": ["personality_analysis", "memory_retrieval", "response_generation", "finalization"],
                "thread_id": thread_id,
            }
            
            # Add relationship data for waifu agents
            if is_waifu and "relationship" in final_state:
                metadata["relationship"] = final_state["relationship"]
            
            return AgentResponse(
                message=response_message,
                confidence=0.9,
                reasoning=response_reasoning,
                metadata=metadata,
                status=AgentStatus.COMPLETED
            )
            
        except Exception as e:
            return AgentResponse(
                message="I apologize, I encountered an error processing your message.",
                confidence=0.0,
                reasoning=f"Workflow error: {str(e)}",
                metadata={
                    "agent_id": agent_id,
                    "provider": "langgraph",
                    "error": str(e)
                },
                status=AgentStatus.ERROR
            )
    
    def update_agent(self, agent_id: str, config: AgentConfiguration) -> None:
        """
        Update an existing agent's configuration.
        
        This recreates the agent with the new configuration.
        
        Args:
            agent_id: Agent identifier
            config: New configuration
        """
        if agent_id in self._graphs:
            del self._graphs[agent_id]
        if agent_id in self._agent_configs:
            del self._agent_configs[agent_id]
        
        # Update the underlying Pydantic AI agent
        self._pydantic_client.update_agent(agent_id, config)
        
        # Recreate the graph
        self.create_agent(agent_id, config)
    
    def remove_agent(self, agent_id: str) -> None:
        """
        Remove an agent and its workflow.
        
        Args:
            agent_id: Agent identifier
        """
        if agent_id in self._graphs:
            del self._graphs[agent_id]
        if agent_id in self._agent_configs:
            del self._agent_configs[agent_id]
        
        # Remove from Pydantic AI client
        self._pydantic_client.remove_agent(agent_id)
    
    async def chat_stream(
        self,
        agent_id: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[AgentResponse]:
        """
        Stream responses through the LangGraph workflow.
        
        This implementation streams the workflow execution, yielding
        responses as each node completes, culminating in the final
        response from the response_generation node.
        
        Args:
            agent_id: Agent identifier
            message: User message
            context: Additional context
            
        Yields:
            AgentResponse objects for each workflow step
        """
        if agent_id not in self._graphs:
            raise ValueError(f"Agent {agent_id} not found")
        
        graph = self._graphs[agent_id]
        config_obj = self._agent_configs.get(agent_id)
        
        # Determine if this is a waifu agent
        is_waifu = (
            config_obj and
            hasattr(config_obj, 'personality') and 
            'waifu' in getattr(config_obj.personality, 'name', '').lower()
        )
        
        # Prepare initial state (same as chat method)
        if is_waifu:
            from models.ai_agent.langgraph_state import PersonalityContext, RelationshipContext
            
            initial_state = WaifuState(
                agent_id=agent_id,
                agent_name=getattr(config_obj.personality, 'name', 'Waifu') if config_obj else 'Waifu',
                user_message=message,
                messages=[],
                personality=PersonalityContext(
                    traits=getattr(config_obj.personality, 'traits', {}) if config_obj else {},
                    mood=getattr(config_obj.personality, 'mood', 'neutral') if config_obj else 'neutral'
                ),
                relationship=RelationshipContext(
                    user_id=context.get('user_id', 'default_user') if context else 'default_user',
                    agent_id=agent_id,
                    affection_level=context.get('affection_level', 50.0) if context else 50.0,
                    relationship_stage=context.get('relationship_stage', 'friend') if context else 'friend'
                ),
                context=context or {}
            )
        else:
            from models.ai_agent.langgraph_state import PersonalityContext
            
            initial_state = ConversationState(
                agent_id=agent_id,
                agent_name=getattr(config_obj.personality, 'name', 'AI') if config_obj else 'AI',
                user_message=message,
                messages=[],
                personality=PersonalityContext(
                    traits=getattr(config_obj.personality, 'traits', {}) if config_obj else {},
                    mood=getattr(config_obj.personality, 'mood', 'neutral') if config_obj else 'neutral'
                ),
                context=context or {}
            )
        
        try:
            thread_id = context.get('thread_id', str(uuid4())) if context else str(uuid4())
            config_dict = {
                "configurable": {"thread_id": thread_id}
            }
            
            # Stream the workflow execution
            async for event in graph.astream(
                initial_state.model_dump(),
                config=config_dict,
                stream_mode="updates"
            ):
                # Each event is a dict with node name as key
                for node_name, node_output in event.items():
                    # Yield intermediate updates
                    if node_name == "response_generation":
                        # This is the main response - stream it
                        response_draft = node_output.get("response_draft", "")
                        if response_draft:
                            yield AgentResponse(
                                message=response_draft,
                                confidence=0.8,
                                reasoning="partial",
                                metadata={
                                    "agent_id": agent_id,
                                    "provider": "langgraph",
                                    "node": node_name,
                                    "streaming": True
                                },
                                status=AgentStatus.RESPONDING
                            )
                    elif node_name == "finalization":
                        # Final response
                        final_message = node_output.get("response_final", "")
                        if final_message:
                            yield AgentResponse(
                                message=final_message,
                                confidence=0.9,
                                reasoning="final",
                                metadata={
                                    "agent_id": agent_id,
                                    "provider": "langgraph",
                                    "node": node_name,
                                    "streaming": False,
                                    "thread_id": thread_id
                                },
                                status=AgentStatus.COMPLETED
                            )
            
        except Exception as e:
            yield AgentResponse(
                message=f"Stream error: {str(e)}",
                confidence=0.0,
                reasoning="error",
                metadata={
                    "agent_id": agent_id,
                    "provider": "langgraph",
                    "error": str(e)
                },
                status=AgentStatus.ERROR
            )
