"""
Homunculy - AI Agent Management System (2026 Architecture).

Main application entry point following Clean Architecture.
Layers: Domain -> Application -> Infrastructure -> Presentation
"""

from common.logger import configure_logging, get_logger
from infrastructure.adapters.elevenlabs import ElevenLabsTTSAdapter
from infrastructure.adapters.langgraph import LangGraphLLMAdapter
from infrastructure.adapters.langgraph.graph_manager import create_graph_manager
from infrastructure.config import get_settings
from infrastructure.persistence import CheckpointerManager, create_postgres_checkpointer
from presentation.http import create_app
from presentation.http.handlers.agent import set_llm_service
from presentation.http.handlers.livekit import configure_livekit

# Configure logging first
configure_logging()
logger = get_logger(__name__)

# Global service instances
_checkpointer_manager: CheckpointerManager | None = None
_llm_adapter: LangGraphLLMAdapter | None = None
_tts_adapter: ElevenLabsTTSAdapter | None = None


async def on_startup() -> None:
    """Initialize services on startup."""
    global _checkpointer_manager, _llm_adapter, _tts_adapter

    settings = get_settings()
    logger.info("Initializing services", app=settings.app.name)

    # Initialize checkpointer
    checkpointer = await create_postgres_checkpointer()
    _checkpointer_manager = CheckpointerManager(checkpointer)
    await _checkpointer_manager.ensure_initialized()

    # Initialize graph manager
    graph_manager = create_graph_manager(
        api_key=settings.llm.api_key,
        checkpointer=checkpointer,
        build_fn=_build_graph,
    )

    # Initialize LLM adapter
    _llm_adapter = LangGraphLLMAdapter(
        api_key=settings.llm.api_key,
        graph_manager=graph_manager,
    )
    set_llm_service(_llm_adapter)

    # Initialize TTS adapter
    if settings.tts.api_key:
        _tts_adapter = ElevenLabsTTSAdapter(settings.tts.api_key)
        logger.info("TTS service initialized")

    # Configure LiveKit
    if settings.livekit.api_key:
        configure_livekit(settings.livekit.api_key, settings.livekit.api_secret)
        logger.info("LiveKit configured")

    logger.info("All services initialized")


async def on_shutdown() -> None:
    """Cleanup services on shutdown."""
    if _checkpointer_manager:
        await _checkpointer_manager.cleanup()
    logger.info("Services cleaned up")


async def _build_graph(api_key: str, checkpointer, config, bind_tools: bool):
    """Build LangGraph workflow (placeholder)."""
    # This would use application.graphs.builder in full implementation
    from application.graphs.state import GraphState
    from langgraph.graph import StateGraph

    graph = StateGraph(GraphState)
    # Add nodes and edges based on config
    return graph.compile(checkpointer=checkpointer)


# Create FastAPI application
settings = get_settings()
app = create_app(
    name=settings.app.name,
    version=settings.app.version,
    on_startup=on_startup,
    on_shutdown=on_shutdown,
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main_new:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.debug,
    )
