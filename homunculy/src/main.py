"""
Homunculy - 2026 Hybrid Dual-System AI Agent.

Clean Architecture entrypoint - ALL dependency wiring happens here.

Architecture:
- ReflexLayer: Fast responses (<300ms) - greetings, acknowledgments
- CognitionLayer: Deep reasoning - LangGraph with tools
- DualSystemOrchestrator: Coordinates both in parallel

Usage:
    python -m main              # Worker mode (LiveKit agent)
    python -m main --api        # API mode (FastAPI server)
"""

from __future__ import annotations

import os
import sys

from common.logger import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)

try:
    from common.telemetry import configure_opentelemetry

    configure_opentelemetry()
except Exception as e:
    logger.debug("OpenTelemetry not configured", error=str(e))


def _env(key: str, default: str = "") -> str:
    """Get environment variable."""
    return os.getenv(key, default)


def _env_int(key: str, default: int = 0) -> int:
    """Get integer environment variable."""
    return int(os.getenv(key, str(default)))


# =============================================================================
# Health Server
# =============================================================================


def _start_health_server(port: int) -> None:
    """Start background health server."""
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from threading import Thread

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            ok = self.path == "/health"
            self.send_response(200 if ok else 404)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"ok" if ok else b"not found")

        def log_message(self, format: str, *args) -> None:  # noqa: A002
            pass

    server = HTTPServer(("0.0.0.0", port), Handler)
    Thread(target=server.serve_forever, daemon=True).start()
    logger.info("Health server started", port=port)


# =============================================================================
# Worker Mode (LiveKit Agent)
# =============================================================================


def run_worker() -> None:
    """Run as LiveKit agent worker.

    Dependencies wired:
    1. Health server (background)
    2. LiveKit worker (foreground)
    """
    _start_health_server(_env_int("HEALTH_PORT", 8000))
    _run_livekit_worker()


def _run_livekit_worker() -> None:
    """Import and run LiveKit worker."""
    from infrastructure.transport.livekit_agent_worker import run_worker as lk_run

    lk_run()


# =============================================================================
# API Mode (FastAPI) - Wires all dependencies
# =============================================================================


def create_api():
    """Create FastAPI app with dependency wiring."""
    from presentation.http import create_app
    from settings import APP_NAME, APP_VERSION

    return create_app(
        name=APP_NAME,
        version=APP_VERSION,
        on_startup=_wire_dependencies,
        on_shutdown=_cleanup_dependencies,
    )


# Global state for cleanup
_state: dict = {}


async def _wire_dependencies() -> None:
    """Wire ALL dependencies at startup.

    Order matters - wire bottom-up:
    1. Persistence (checkpointer)
    2. Core adapters (orchestrator, LLM, TTS)
    3. Dual-system (reflex + cognition)
    4. Container overrides
    """
    from infrastructure.adapters.factory import (
        create_cognition,
        create_dual_system,
        create_emotion_detector,
        create_orchestrator,
        create_reflex,
    )
    from infrastructure.container import container

    # 1. Persistence
    _state["checkpointer"] = await _create_checkpointer()
    container.checkpointer.override(_state["checkpointer"].checkpointer)

    # 2. Core adapters
    orchestrator = create_orchestrator()

    # 3. Dual-system
    reflex = create_reflex()
    cognition = create_cognition(orchestrator=orchestrator)
    emotion = create_emotion_detector()
    dual_system = create_dual_system(reflex, cognition, emotion)

    # 4. Override container (for handlers to access via DI)
    container.orchestrator.override(lambda: orchestrator)
    container.dual_system.override(lambda: dual_system)

    logger.info("Dependencies wired", mode="api")


async def _cleanup_dependencies() -> None:
    """Cleanup dependencies at shutdown."""
    if cp := _state.get("checkpointer"):
        await cp.cleanup()
    logger.info("Dependencies cleaned up")


async def _create_checkpointer():
    """Create checkpointer (Postgres or memory)."""
    from infrastructure.persistence import CheckpointerFactory

    if _env("DB_HOST"):
        return await CheckpointerFactory.create_postgres(_build_db_url())
    return CheckpointerFactory.create_memory()


def _build_db_url() -> str:
    """Build database URL from environment."""
    host = _env("DB_HOST", "localhost")
    port = _env("DB_PORT", "5432")
    name = _env("DB_NAME", "homunculy")
    user = _env("DB_USER", "postgres")
    password = _env("DB_PASSWORD", "")
    return f"postgresql://{user}:{password}@{host}:{port}/{name}"


# FastAPI app instance (for uvicorn)
app = create_api()


# =============================================================================
# CLI Entrypoint
# =============================================================================


def main() -> None:
    """CLI entrypoint."""
    if "--api" in sys.argv:
        _run_api_server()
    else:
        run_worker()


def _run_api_server() -> None:
    """Run FastAPI server."""
    import uvicorn

    from settings import settings

    uvicorn.run(
        "main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.debug,
    )


if __name__ == "__main__":
    main()
