"""LangGraph helper functions."""

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from domain.entities import AgentConfiguration


def runnable_config(thread_id: str) -> dict[str, Any]:
    """Create runnable config with thread ID."""
    return {"configurable": {"thread_id": thread_id}}


async def is_first_message(graph: Any, config: dict, thread_id: str) -> bool:
    """Check if this is the first message in thread."""
    state = await graph.aget_state(config)
    return _state_is_empty(state)


def _state_is_empty(state: Any) -> bool:
    """Check if state has no messages."""
    if not state or not state.values:
        return True
    return len(state.values.get("messages", [])) == 0


def build_messages(
    config: AgentConfiguration,
    message: str,
    is_first: bool,
) -> list[Any]:
    """Build message list for graph invocation."""
    messages = []
    if is_first and config.system_prompt:
        messages.append(_system_message(config))
    messages.append(_human_message(message))
    return messages


def _system_message(config: AgentConfiguration) -> SystemMessage:
    """Create system message from config."""
    return SystemMessage(content=config.system_prompt)


def _human_message(message: str) -> HumanMessage:
    """Create human message."""
    return HumanMessage(content=message)


async def invoke_graph(graph: Any, messages: list, config: dict) -> dict:
    """Invoke graph and return result."""
    result = await graph.ainvoke({"messages": messages}, config)
    return result


async def stream_graph(
    graph: Any,
    config: AgentConfiguration,
    message: str,
    thread_id: str,
):
    """Stream graph response chunks."""
    run_config = runnable_config(thread_id)
    is_first = await is_first_message(graph, run_config, thread_id)
    messages = build_messages(config, message, is_first)

    async for event in graph.astream_events(
        {"messages": messages},
        run_config,
        version="v2",
    ):
        chunk = _extract_chunk(event)
        if chunk:
            yield chunk


def _extract_chunk(event: dict) -> str | None:
    """Extract text chunk from stream event."""
    if event.get("event") != "on_chat_model_stream":
        return None
    data = event.get("data", {})
    chunk = data.get("chunk")
    if chunk and hasattr(chunk, "content"):
        return chunk.content
    return None


def extract_response(result: dict) -> str:
    """Extract response text from graph result."""
    messages = result.get("messages", [])
    if not messages:
        return ""
    last = messages[-1]
    return _get_content(last)


def _get_content(message: Any) -> str:
    """Get content from message."""
    if hasattr(message, "content"):
        return message.content
    return str(message)
