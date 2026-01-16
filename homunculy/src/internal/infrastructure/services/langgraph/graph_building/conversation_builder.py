"""LangGraph conversation flow builders."""

from typing import Any, Dict, List, Optional, Sequence, Union

from langchain_core.messages import AIMessage, AnyMessage, BaseMessage, HumanMessage
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from pydantic import SecretStr

from internal.domain.entities import AgentConfiguration


class ConversationState(MessagesState):
    """LangGraph state with summarization support."""

    context: Dict[str, Any]
    llm_input_messages: List[AnyMessage]
    response: Optional[str]
    error: Optional[str]
    tools: Optional[List[Any]]  # Store tools for tool node


def create_langchain_model(
    api_key: str,
    model_name: str,
    temperature: float = 0.7,
    max_tokens: int = 1000,
) -> ChatOpenAI:
    """Create ChatOpenAI model."""
    return ChatOpenAI(
        model=model_name,
        api_key=SecretStr(api_key),
        temperature=temperature,
        max_completion_tokens=max_tokens,
    )


def build_system_prompt(configuration: AgentConfiguration) -> str:
    """Build system prompt from configuration."""
    p = configuration.personality
    personality = f"You are {p.name}. {p.description}. Your mood is {p.mood}."
    base = (configuration.system_prompt or "").strip()
    return f"{base}\n\n{personality}".strip()


def _create_llm_node(llm: Union[ChatOpenAI, Runnable], use_summarized: bool = True):
    """Create LLM invocation node.

    Args:
        llm: The language model to use
        use_summarized: If True, use llm_input_messages (from summarizer).
                       If False, use messages directly (for tool follow-up).
    """
    from common.logger import get_logger

    logger = get_logger(__name__)

    async def call_llm(state: ConversationState) -> Dict[str, Any]:
        if use_summarized:
            messages = state.get("llm_input_messages") or state.get("messages", [])
        else:
            messages = state.get("messages", [])

        if not messages:
            return {"error": "No messages", "response": None}

        try:
            result = await llm.ainvoke(messages)
            content = result.content if hasattr(result, "content") else str(result)

            if isinstance(result, AIMessage):
                tool_calls = getattr(result, "tool_calls", None)
                if tool_calls:
                    return {"messages": [result], "error": None}

            return {"response": content, "messages": [result], "error": None}
        except Exception as exc:
            logger.error("LLM failed", error=str(exc), exc_info=True)
            return {"error": str(exc), "response": None}

    return call_llm


def _create_token_counter(llm: Union[ChatOpenAI, Runnable]):
    """Create token counter for summarization."""

    def count_tokens(messages) -> int:
        converted = [_convert_message(m) for m in messages]
        if isinstance(llm, ChatOpenAI) and converted:
            return llm.get_num_tokens_from_messages(converted)
        return len(str(converted)) // 4

    return count_tokens


def _convert_message(msg) -> BaseMessage:
    """Convert dict to BaseMessage if needed."""
    if isinstance(msg, BaseMessage):
        return msg
    role = msg.get("role", "user")
    content = msg.get("content", "")
    return AIMessage(content=content) if role == "assistant" else HumanMessage(content=content)


def _get_summarization_model(llm: Union[ChatOpenAI, Runnable], max_tokens: int):
    """Get model for summarization."""
    if isinstance(llm, ChatOpenAI):
        return llm.bind(max_tokens=max_tokens)
    return llm


def _should_continue_after_llm(state: ConversationState) -> str:
    """Determine if we should continue to tools or end."""
    messages = state.get("messages", [])
    if not messages:
        return END

    last_message = messages[-1]

    if isinstance(last_message, AIMessage):
        tool_calls = getattr(last_message, "tool_calls", None)
        if tool_calls:
            return "tools"

    return END


def build_conversation_graph_with_summarization(
    llm: Union[ChatOpenAI, Runnable],
    system_prompt: str,
    max_tokens: int = 256,
    max_tokens_before_summary: int = 1024,
    max_summary_tokens: int = 128,
    checkpointer=None,
    tools: Optional[Sequence[BaseTool]] = None,
):
    """Compile conversation graph with LangMem summarization and tool support.

    Graph structure:
    - Without tools: START → summarize → llm → END
    - With tools: START → summarize → llm → (tools → llm_tool_followup)* → END
    """
    from langmem.short_term import SummarizationNode

    summarization_node = SummarizationNode(
        token_counter=_create_token_counter(llm),
        model=_get_summarization_model(llm, max_summary_tokens),
        max_tokens=max_tokens,
        max_tokens_before_summary=max_tokens_before_summary,
        max_summary_tokens=max_summary_tokens,
        input_messages_key="messages",
        output_messages_key="llm_input_messages",
    )

    graph = StateGraph(ConversationState)
    graph.add_node("summarize", summarization_node)
    graph.add_node("llm", _create_llm_node(llm, use_summarized=True))
    graph.add_edge(START, "summarize")
    graph.add_edge("summarize", "llm")

    if tools:
        tool_node = ToolNode(tools)
        graph.add_node("tools", tool_node)
        # Separate LLM node for after tools - uses messages directly
        graph.add_node("llm_tool_followup", _create_llm_node(llm, use_summarized=False))

        # After initial LLM, check if we need to run tools
        graph.add_conditional_edges("llm", _should_continue_after_llm, ["tools", END])
        # After tools, go to tool followup LLM
        graph.add_edge("tools", "llm_tool_followup")
        # After tool followup, check again (might need more tools or end)
        graph.add_conditional_edges("llm_tool_followup", _should_continue_after_llm, ["tools", END])
    else:
        graph.add_edge("llm", END)

    return graph.compile(checkpointer=checkpointer)
