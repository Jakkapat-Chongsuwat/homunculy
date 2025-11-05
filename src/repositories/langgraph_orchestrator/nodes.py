"""
LangGraph Node Definitions.

This module defines node functions for LangGraph workflows.
Each node is a pure function that takes state and returns updated state,
following functional programming principles and Clean Architecture.

Nodes use Pydantic AI agents for LLM operations, making this module
the bridge between LangGraph orchestration and Pydantic AI execution.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone

from models.ai_agent.langgraph_state import ConversationState, WaifuState, ConversationMessage
from repositories.pydantic_ai_client.pydantic_ai_client import PydanticAILLMClient
from models.ai_agent.ai_agent import AgentConfiguration, AgentProvider, AgentPersonality


class LangGraphNodeFunctions:
    """
    Collection of LangGraph node functions.
    
    Each method is a node in the LangGraph workflow. Nodes are stateless
    functions that receive state, perform operations (potentially using
    Pydantic AI agents), and return updated state.
    """
    
    def __init__(self, llm_client: Optional[PydanticAILLMClient] = None):
        """Initialize with an optional LLM client."""
        self._llm_client = llm_client or PydanticAILLMClient()
    
    async def personality_analysis_node(
        self,
        state: ConversationState
    ) -> Dict[str, Any]:
        """
        Analyze user message and update personality/emotional context.
        
        This node uses a Pydantic AI agent specialized in personality
        analysis to understand the emotional tone and adjust the agent's
        personality state accordingly.
        
        Args:
            state: Current conversation state
            
        Returns:
            Dictionary with updated personality context
        """
        # Create a specialized personality analyzer agent
        analyzer_config = AgentConfiguration(
            provider=AgentProvider.PYDANTIC_AI,
            model_name="gpt-4",
            personality=AgentPersonality(
                name="Personality Analyzer",
                description="Analyzes emotional tone and personality context",
                traits={"analytical": 0.9, "empathetic": 0.8}
            ),
            system_prompt="""You are a personality and emotion analyzer.
            Analyze the user's message and provide:
            1. Emotional tone (positive, negative, neutral)
            2. Intensity level (0.0-1.0)
            3. Key emotional keywords
            
            Respond in JSON format:
            {
                "tone": "positive|negative|neutral",
                "intensity": 0.0-1.0,
                "keywords": ["word1", "word2"],
                "suggested_mood": "happy|sad|neutral|excited|calm"
            }
            """,
            temperature=0.3,
        )
        
        # Register the analyzer agent if not already registered
        analyzer_id = f"{state.agent_id}_personality_analyzer"
        try:
            self._llm_client.create_agent(analyzer_id, analyzer_config)
        except Exception:
            pass  # Agent already exists
        
        # Analyze the user message
        try:
            analysis_prompt = f"Analyze this message: '{state.user_message}'"
            _result = await self._llm_client.chat(
                agent_id=analyzer_id,
                message=analysis_prompt,
                context={"conversation_history": str(state.messages[-3:] if state.messages else [])}
            )
            
            # Parse result and update personality context
            # In a real implementation, you'd parse JSON from the response
            personality_updates = {
                "personality": {
                    "mood": "responsive",  # Would extract from analysis
                    "emotional_state": {"engagement": 0.7},
                    "memory_summary": f"User said: {state.user_message[:50]}..."
                }
            }
            
            return personality_updates
            
        except Exception:
            # Fallback to neutral personality
            return {
                "personality": {
                    "mood": "neutral",
                    "emotional_state": {},
                    "memory_summary": ""
                }
            }
    
    async def memory_retrieval_node(
        self,
        state: ConversationState
    ) -> Dict[str, Any]:
        """
        Retrieve relevant memories and conversation context.
        
        This node uses a Pydantic AI agent to analyze conversation history
        and retrieve relevant context for response generation.
        
        Args:
            state: Current conversation state
            
        Returns:
            Dictionary with relevant memory context
        """
        # Create memory retrieval agent
        memory_config = AgentConfiguration(
            provider=AgentProvider.PYDANTIC_AI,
            model_name="gpt-4",
            personality=AgentPersonality(
                name="Memory Retriever",
                description="Retrieves relevant conversation context",
                traits={"memory": 0.95, "contextual": 0.9}
            ),
            system_prompt="""You are a memory and context specialist.
            Given a conversation history and current message, identify:
            1. Relevant previous topics
            2. User preferences mentioned
            3. Important context for response
            
            Provide a concise summary of relevant memories.
            """,
            temperature=0.2,
        )
        
        memory_id = f"{state.agent_id}_memory_retriever"
        try:
            self._llm_client.create_agent(memory_id, memory_config)
        except Exception:
            pass
        
        # Build conversation summary
        recent_messages = state.messages[-5:] if state.messages else []
        history_text = "\n".join([
            f"{msg.role}: {msg.content}" 
            for msg in recent_messages
        ])
        
        try:
            memory_prompt = f"""
            Conversation history:
            {history_text}
            
            Current message: {state.user_message}
            
            What context is most relevant for responding?
            """
            
            memory_result = await self._llm_client.chat(
                agent_id=memory_id,
                message=memory_prompt,
                context={"agent_id": state.agent_id}
            )
            
            return {
                "context": {
                    "memory_summary": memory_result.message,
                    "relevant_topics": [],  # Would extract from analysis
                }
            }
            
        except Exception:
            return {
                "context": {
                    "memory_summary": "No prior context available",
                    "relevant_topics": [],
                }
            }
    
    async def response_generation_node(
        self,
        state: ConversationState
    ) -> Dict[str, Any]:
        """
        Generate the main response using Pydantic AI agent.
        
        This is the core response generation node that uses the main
        agent with full personality and context to create the response.
        
        Args:
            state: Current conversation state with personality and memory
            
        Returns:
            Dictionary with generated response
        """
        # Use the main agent for response generation
        try:
            # Build enriched context
            enriched_context = {
                "personality": state.personality.model_dump() if hasattr(state, 'personality') else {},
                "mood": state.personality.mood if hasattr(state, 'personality') else "neutral",
                "memory": state.context.get("memory_summary", ""),
                "conversation_history": [
                    {"role": msg.role, "content": msg.content}
                    for msg in state.messages[-3:]
                ] if state.messages else []
            }
            
            # Generate response with main agent
            result = await self._llm_client.chat(
                agent_id=state.agent_id,
                message=state.user_message,
                context=enriched_context
            )
            
            return {
                "response_draft": result.message,
                "response_reasoning": result.reasoning or "Generated based on context",
                "current_node": "response_generation"
            }
            
        except Exception as e:
            return {
                "response_draft": f"I apologize, I'm having trouble responding right now.",
                "response_reasoning": f"Error: {str(e)}",
                "current_node": "response_generation"
            }
    
    async def relationship_update_node(
        self,
        state: WaifuState
    ) -> Dict[str, Any]:
        """
        Update relationship metrics based on interaction (Waifu-specific).
        
        This node analyzes the conversation and updates relationship
        metrics like affection level, relationship stage, etc.
        
        Args:
            state: Current waifu state
            
        Returns:
            Dictionary with updated relationship context
        """
        if not state.relationship:
            # No relationship to update
            return {}
        
        # Create relationship analyzer
        rel_config = AgentConfiguration(
            provider=AgentProvider.PYDANTIC_AI,
            model_name="gpt-4",
            personality=AgentPersonality(
                name="Relationship Analyzer",
                description="Analyzes relationship dynamics",
                traits={"empathy": 0.95, "social": 0.9}
            ),
            system_prompt="""You are a relationship dynamics expert.
            Analyze the interaction and determine:
            1. Affection change (-5 to +5)
            2. Relationship quality (improving/stable/declining)
            3. Notable interaction elements
            
            Respond with: affection_change, quality, notes
            """,
            temperature=0.4,
        )
        
        rel_id = f"{state.agent_id}_relationship_analyzer"
        try:
            self._llm_client.create_agent(rel_id, rel_config)
        except Exception:
            pass
        
        try:
            analysis_prompt = f"""
            User message: {state.user_message}
            Agent response: {state.response_draft}
            Current affection: {state.relationship.affection_level}
            Relationship stage: {state.relationship.relationship_stage}
            
            How should this interaction affect the relationship?
            """
            
            _rel_result = await self._llm_client.chat(
                agent_id=rel_id,
                message=analysis_prompt,
                context={}
            )
            
            # In real implementation, parse the response for metrics
            # For now, apply simple logic
            affection_change = 0.5  # Small positive interaction
            new_affection = min(100.0, state.relationship.affection_level + affection_change)
            
            # Determine relationship stage
            new_stage = state.relationship.relationship_stage
            if new_affection > 80:
                new_stage = "romantic"
            elif new_affection > 60:
                new_stage = "close_friend"
            elif new_affection > 40:
                new_stage = "friend"
            elif new_affection > 20:
                new_stage = "acquaintance"
            
            return {
                "relationship": {
                    "affection_level": new_affection,
                    "relationship_stage": new_stage,
                    "interaction_count": state.relationship.interaction_count + 1,
                    "last_interaction": datetime.now(timezone.utc),
                    "relationship_notes": f"Recent interaction: positive"
                }
            }
            
        except Exception:
            # Minimal update on error
            return {
                "relationship": {
                    "interaction_count": state.relationship.interaction_count + 1,
                    "last_interaction": datetime.now(timezone.utc),
                }
            }
    
    async def response_finalization_node(
        self,
        state: ConversationState
    ) -> Dict[str, Any]:
        """
        Finalize the response and prepare for output.
        
        This node performs final checks, formatting, and adds the
        response to the conversation history.
        
        Args:
            state: Current conversation state with draft response
            
        Returns:
            Dictionary with finalized response and updated messages
        """
        # Add user message to history
        user_msg = ConversationMessage(
            role="user",
            content=state.user_message,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Add assistant response to history
        assistant_msg = ConversationMessage(
            role="assistant",
            content=state.response_draft,
            timestamp=datetime.now(timezone.utc),
            metadata={
                "reasoning": state.response_reasoning,
                "personality_mood": state.personality.mood if hasattr(state, 'personality') else "neutral"
            }
        )
        
        updated_messages = state.messages + [user_msg, assistant_msg]
        
        return {
            "response_final": state.response_draft,
            "messages": updated_messages,
            "current_node": "finalization",
            "next_node": None  # End of workflow
        }


# Routing functions for conditional edges
def should_update_relationship(state: Dict[str, Any]) -> str:
    """
    Determine if relationship should be updated.
    
    This is a routing function used by LangGraph for conditional edges.
    
    Args:
        state: Current state dictionary
        
    Returns:
        Next node name: "relationship_update" or "finalization"
    """
    # Check if this is a waifu state with relationship context
    if "relationship" in state and state["relationship"] is not None:
        return "relationship_update"
    return "finalization"


def should_continue_workflow(state: Dict[str, Any]) -> str:
    """
    Determine if workflow should continue or end.
    
    Args:
        state: Current state dictionary
        
    Returns:
        "continue" or "end"
    """
    if state.get("next_node") is None:
        return "end"
    return "continue"
