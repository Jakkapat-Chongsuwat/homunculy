"""Per-session LiveKit + Pipecat runner (subprocess entrypoint)."""

from __future__ import annotations

import argparse
import asyncio
import os
from typing import Any

from common.logger import configure_logging, get_logger
from domain.entities.agent import AgentConfiguration, AgentPersonality, AgentProvider
from infrastructure.adapters.langgraph import LangGraphLLMAdapter, LangGraphPipecatService
from infrastructure.adapters.langgraph.graph_manager import create_graph_manager
from infrastructure.config import get_settings
from infrastructure.persistence import CheckpointerFactory, CheckpointerUnitOfWork
from infrastructure.transport.pipecat_pipeline import create_pipeline

logger = get_logger(__name__)


def main() -> None:
    """CLI entrypoint."""
    configure_logging()
    args = _parse_args()
    asyncio.run(_run(args))


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run isolated LiveKit session")
    p.add_argument("--url")
    p.add_argument("--token")
    p.add_argument("--room")
    p.add_argument("--session-id")
    return p.parse_args()


async def _run(args: argparse.Namespace) -> None:
    url = _value(args.url, "LIVEKIT_URL")
    token = _value(args.token, "LIVEKIT_TOKEN")
    room = _value(args.room, "LIVEKIT_ROOM")
    session_id = _value(args.session_id, "HOMUNCULY_SESSION_ID")
    await _run_session(url, token, room, session_id)


def resolve_value(value: str | None, env: str) -> str:
    """Public wrapper for env resolution (test hook)."""
    return _value(value, env)


def _value(value: str | None, env: str) -> str:
    resolved = value or os.getenv(env, "")
    if resolved:
        return resolved
    raise SystemExit(f"Missing {env}")


async def _run_session(url: str, token: str, room: str, session_id: str) -> None:
    logger.info("Session start", room=room, session_id=session_id)
    _patch_livekit_room()
    uow = await _create_checkpointer()
    try:
        await _start_pipeline(uow, url, token, room, session_id)
    finally:
        await uow.cleanup()


async def _create_checkpointer() -> CheckpointerUnitOfWork:
    if os.getenv("DB_HOST"):
        return await CheckpointerFactory.create_postgres(_conn_string())
    return CheckpointerFactory.create_memory()


def connection_string() -> str:
    """Public wrapper for connection string (test hook)."""
    return _conn_string()


def _conn_string() -> str:
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "homunculy")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "")
    return f"postgresql://{user}:{password}@{host}:{port}/{name}"


def _patch_livekit_room() -> None:
    room = _room_class()
    if not room:
        return
    room._on_room_event = _safe_room_event(room._on_room_event)


def _room_class():
    try:
        from livekit.rtc.room import Room
    except Exception:
        return None
    return Room


def _safe_room_event(fn):
    def wrapped(self, event):
        try:
            return fn(self, event)
        except KeyError:
            return None

    return wrapped


async def _start_pipeline(
    uow: CheckpointerUnitOfWork,
    url: str,
    token: str,
    room: str,
    session_id: str,
) -> None:
    await uow.setup()
    service = await _llm_service(uow, session_id)
    pipeline = create_pipeline(service)
    await pipeline.run_with_parts(url, token, room)


async def run_session(url: str, token: str, room: str, session_id: str) -> None:
    """Public wrapper for session run (test hook)."""
    await _run_session(url, token, room, session_id)


async def _llm_service(uow: CheckpointerUnitOfWork, session_id: str) -> Any:
    settings = get_settings()
    graph = create_graph_manager(settings.llm.api_key, uow.checkpointer, _build_graph)
    adapter = LangGraphLLMAdapter(settings.llm.api_key, graph)
    config = _agent_config(settings)
    return LangGraphPipecatService(adapter, config, session_id)


def _agent_config(settings) -> AgentConfiguration:
    return AgentConfiguration(
        provider=AgentProvider.LANGRAPH,
        model_name=settings.llm.model,
        personality=_personality(),
        temperature=settings.llm.temperature,
        max_tokens=settings.llm.max_tokens,
    )


def _personality() -> AgentPersonality:
    return AgentPersonality(
        name="Homunculy",
        description="LiveKit voice agent",
        traits={},
    )


async def _build_graph(api_key: str, checkpointer, config, bind_tools: bool):
    graph = _graph(_llm(api_key, config.model_name))
    return graph.compile(checkpointer=checkpointer)


def _graph(llm):
    from langgraph.graph import END, START, StateGraph

    from application.graphs.state import GraphState

    graph = StateGraph(GraphState)
    graph.add_node("chat", _chat_node(llm))
    graph.add_edge(START, "chat")
    graph.add_edge("chat", END)
    return graph


def _llm(api_key: str, model: str):
    from langchain_openai import ChatOpenAI
    from pydantic import SecretStr

    return ChatOpenAI(api_key=SecretStr(api_key), model=model)


def _chat_node(llm):
    async def node(state):
        response = await llm.ainvoke(state["messages"])
        return {"messages": [response]}

    return node


if __name__ == "__main__":
    main()
