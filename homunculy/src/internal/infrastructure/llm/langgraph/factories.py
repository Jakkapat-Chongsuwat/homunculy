"""Reusable LangGraph helpers for building conversation flows."""

from typing import Annotated, Any, Dict, List, Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, AIMessage
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.graph.message import add_messages
from pydantic import SecretStr
from typing_extensions import TypedDict

from internal.domain.entities import AgentConfiguration


class ConversationState(MessagesState):
    """Structured LangGraph state compatible with LangMem."""

    context: Dict[str, Any]
    response: Optional[str]
    error: Optional[str]


def create_langchain_model(api_key: str, model_name: str, temperature: float = 0.7, max_tokens: int = 1000) -> ChatOpenAI:
    """Create a LangChain ChatOpenAI model for conversations."""
    return ChatOpenAI(
        model=model_name,
        api_key=SecretStr(api_key),
        temperature=temperature,
        max_completion_tokens=max_tokens,
    )


def _build_personality_context(configuration: AgentConfiguration) -> str:
    """Build personality instruction snippet from configuration."""
    personality = configuration.personality
    return (
        f"You are {personality.name}. {personality.description}. "
        f"Your current mood is {personality.mood}."
    )


def build_system_prompt(configuration: AgentConfiguration) -> str:
    """Build complete system prompt from configuration."""
    base_prompt = (configuration.system_prompt or "").strip()
    personality_context = _build_personality_context(configuration)
    return f"{base_prompt}\n\n{personality_context}".strip()


def create_llm_node(llm: ChatOpenAI):
    """Create LangGraph node using ChatOpenAI directly."""

    async def call_llm(state: ConversationState) -> Dict[str, Any]:
        if not state.get("messages"):
            return {"error": "No messages in conversation", "response": None}

        try:
            # Get messages from state (system message already included by caller)
            messages = state.get("messages", [])
            
            # Call LLM with full conversation history
            result = await llm.ainvoke(messages)
            response_text = result.content
            
            # Return AIMessage so MessagesState.add_messages appends correctly
            return {
                "response": response_text,
                "messages": [result],  # result is already an AIMessage
                "error": None,
            }
        except Exception as exc:  # pragma: no cover - surfaced upstream
            return {"error": str(exc), "response": None}

    return call_llm


def build_conversation_graph_with_summarization(
    llm: ChatOpenAI,
    system_prompt: str,
    max_tokens: int = 256,
    max_tokens_before_summary: int = 1024,
    max_summary_tokens: int = 128,
    checkpointer=None,
):
    """Compile conversation graph with LangMem SummarizationNode integrated."""
    from langchain_core.messages import BaseMessage
    from langmem.short_term import SummarizationNode

    def count_tokens(messages):
        """Token counter wrapper that handles type conversion."""
        converted = []
        for msg in messages:
            if isinstance(msg, BaseMessage):
                converted.append(msg)
            elif isinstance(msg, dict):
                from langchain_core.messages import HumanMessage, AIMessage
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "assistant":
                    converted.append(AIMessage(content=content))
                else:
                    converted.append(HumanMessage(content=content))
        return llm.get_num_tokens_from_messages(converted) if converted else 0

    summarization_model = llm.bind(max_tokens=max_summary_tokens)
    summarization_node = SummarizationNode(
        token_counter=count_tokens,
        model=summarization_model,
        max_tokens=max_tokens,
        max_tokens_before_summary=max_tokens_before_summary,
        max_summary_tokens=max_summary_tokens,
    )

    graph_builder = StateGraph(ConversationState)
    graph_builder.add_node("summarize", summarization_node)
    graph_builder.add_node("llm", create_llm_node(llm))
    graph_builder.add_edge(START, "summarize")
    graph_builder.add_edge("summarize", "llm")
    graph_builder.add_edge("llm", END)
    return graph_builder.compile(checkpointer=checkpointer)
