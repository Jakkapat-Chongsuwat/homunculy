"""
Homunculy - AI Agent (2026 Architecture).

Clean Architecture entrypoint with pluggable transport.
Run modes: worker (default), api

Usage:
    python -m main           # Worker mode (LiveKit agent)
    python -m main --api     # API mode (FastAPI server)
"""

from __future__ import annotations

import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from typing import Protocol, runtime_checkable

from common.logger import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


# =============================================================================
# Transport Interface (Domain Layer)
# =============================================================================


@runtime_checkable
class TransportPort(Protocol):
    """Transport runtime contract."""

    def run(self) -> None:
        """Start the transport."""
        ...


# =============================================================================
# Transport Factory (Application Layer)
# =============================================================================


def create_transport(name: str) -> TransportPort:
    """Create transport by name."""
    if name == "livekit":
        return _livekit()
    raise SystemExit(f"Unknown transport: {name}")


def _livekit():
    from infrastructure.transport.livekit_worker import create_worker

    return create_worker()


# =============================================================================
# Health Server (Infrastructure Layer - Inline)
# =============================================================================


def start_health(port: int) -> None:
    """Start background health server."""
    server = HTTPServer(("0.0.0.0", port), _HealthHandler)
    Thread(target=server.serve_forever, daemon=True).start()
    logger.info("Health server started", port=port)


class _HealthHandler(BaseHTTPRequestHandler):
    """Minimal /health endpoint."""

    def do_GET(self) -> None:
        code, body = (200, b"ok") if self.path == "/health" else (404, b"not found")
        self.send_response(code)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        pass


# =============================================================================
# Worker Mode
# =============================================================================


def run_worker() -> None:
    """Run as LiveKit agent service.

    Agent runs as HTTP service (FastAPI) with:
    - POST /join - Control Plane tells agent to join a room
    - POST /leave - Control Plane tells agent to leave
    - GET /health - Health check
    - GET /sessions - List active sessions
    """
    transport = create_transport(os.getenv("AGENT_TRANSPORT", "livekit"))
    transport.run()


# =============================================================================
# API Mode (Legacy FastAPI)
# =============================================================================


def create_api():
    """Create FastAPI app for API mode."""
    from infrastructure.config import get_settings
    from presentation.http import create_app

    settings = get_settings()
    return create_app(
        name=settings.app.name,
        version=settings.app.version,
        on_startup=_api_startup,
        on_shutdown=_api_shutdown,
    )


_checkpointer_uow = None


async def _api_startup() -> None:
    """Initialize API services."""
    global _checkpointer_uow

    from infrastructure.adapters.elevenlabs import ElevenLabsTTSAdapter
    from infrastructure.adapters.langgraph import LangGraphLLMAdapter
    from infrastructure.adapters.langgraph.graph_manager import create_graph_manager
    from infrastructure.config import get_settings
    from infrastructure.container import container
    from presentation.http.handlers.agent import set_llm_service

    settings = get_settings()
    logger.info("Initializing API", app=settings.app.name)

    _checkpointer_uow = await _create_checkpointer()
    await _checkpointer_uow.setup()

    graph_manager = create_graph_manager(
        api_key=settings.llm.api_key,
        checkpointer=_checkpointer_uow.checkpointer,
        build_fn=_build_graph,
    )

    llm_adapter = LangGraphLLMAdapter(
        api_key=settings.llm.api_key,
        graph_manager=graph_manager,
    )
    container.llm_adapter.override(llm_adapter)
    set_llm_service(llm_adapter)

    if settings.tts.api_key:
        container.tts_adapter.override(ElevenLabsTTSAdapter(settings.tts.api_key))
        logger.info("TTS initialized")

    logger.info("API ready")


async def _api_shutdown() -> None:
    """Cleanup API services."""
    if _checkpointer_uow:
        await _checkpointer_uow.cleanup()
    logger.info("API shutdown")


async def _create_checkpointer():
    """Create checkpointer based on environment."""
    from infrastructure.persistence import CheckpointerFactory

    db_host = os.getenv("DB_HOST", "")
    if db_host:
        conn = _db_url()
        return await CheckpointerFactory.create_postgres(conn)
    return CheckpointerFactory.create_memory()


def _db_url() -> str:
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "homunculy")
    user = os.getenv("DB_USER", "postgres")
    pw = os.getenv("DB_PASSWORD", "")
    return f"postgresql://{user}:{pw}@{host}:{port}/{name}"


async def _build_graph(api_key: str, checkpointer, config, bind_tools: bool):
    """Build chat graph."""
    from langchain_openai import ChatOpenAI
    from langgraph.graph import END, START, StateGraph
    from pydantic import SecretStr

    from application.graphs.state import GraphState

    llm = ChatOpenAI(api_key=SecretStr(api_key), model="gpt-4o-mini")

    async def chat(state: GraphState) -> dict:
        return {"messages": [await llm.ainvoke(state["messages"])]}

    g = StateGraph(GraphState)
    g.add_node("chat", chat)
    g.add_edge(START, "chat")
    g.add_edge("chat", END)
    return g.compile(checkpointer=checkpointer)


# FastAPI app instance (for uvicorn)
app = create_api()


# =============================================================================
# CLI Entrypoint
# =============================================================================


def main() -> None:
    """CLI entrypoint."""
    import sys

    if "--api" in sys.argv:
        _run_api()
    else:
        run_worker()


def _run_api() -> None:
    import uvicorn

    from infrastructure.config import get_settings

    settings = get_settings()
    uvicorn.run(
        "main:app", host=settings.app.host, port=settings.app.port, reload=settings.app.debug
    )


if __name__ == "__main__":
    main()
