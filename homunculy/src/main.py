"""
Homunculy - AI Agent Management System (2026 Architecture).

Main application entry point following Clean Architecture.
Layers: Domain -> Application -> Infrastructure -> Presentation

Uses Dependency Injection for clean, testable code.
"""

from common.logger import configure_logging, get_logger
from infrastructure.adapters.elevenlabs import ElevenLabsTTSAdapter
from infrastructure.adapters.langgraph import LangGraphLLMAdapter
from infrastructure.adapters.langgraph.graph_manager import create_graph_manager
from infrastructure.config import get_settings
from infrastructure.container import container
from infrastructure.persistence import CheckpointerFactory, CheckpointerUnitOfWork
from presentation.http import create_app
from presentation.http.handlers.agent import set_llm_service

configure_logging()
logger = get_logger(__name__)

# Application state (managed by lifespan, not global mutable)
_checkpointer_uow: CheckpointerUnitOfWork | None = None


async def on_startup() -> None:
    """Initialize services on startup via DI container."""
    global _checkpointer_uow

    settings = get_settings()
    logger.info("Initializing services", app=settings.app.name)

    # Create checkpointer via factory
    _checkpointer_uow = await _create_checkpointer()
    await _checkpointer_uow.setup()

    # Wire up graph manager
    graph_manager = create_graph_manager(
        api_key=settings.llm.api_key,
        checkpointer=_checkpointer_uow.checkpointer,
        build_fn=_build_graph,
    )

    # Create and register LLM adapter
    llm_adapter = LangGraphLLMAdapter(
        api_key=settings.llm.api_key,
        graph_manager=graph_manager,
    )
    container.llm_adapter.override(llm_adapter)
    set_llm_service(llm_adapter)

    # Create TTS adapter if configured
    if settings.tts.api_key:
        tts_adapter = ElevenLabsTTSAdapter(settings.tts.api_key)
        container.tts_adapter.override(tts_adapter)
        logger.info("TTS service initialized")

    logger.info("All services initialized")


async def on_shutdown() -> None:
    """Cleanup services on shutdown."""
    if _checkpointer_uow:
        await _checkpointer_uow.cleanup()
    logger.info("Services cleaned up")


async def _create_checkpointer() -> CheckpointerUnitOfWork:
    """Create checkpointer based on environment."""
    import os

    db_host = os.getenv("DB_HOST", "")
    if db_host:
        conn_string = _build_connection_string()
        return await CheckpointerFactory.create_postgres(conn_string)
    return CheckpointerFactory.create_memory()


def _build_connection_string() -> str:
    """Build PostgreSQL connection string."""
    import os

    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "homunculy")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "")
    return f"postgresql://{user}:{password}@{host}:{port}/{name}"


async def _build_graph(api_key: str, checkpointer, config, bind_tools: bool):
    """Build simple chat graph with LLM node."""
    from langchain_openai import ChatOpenAI
    from langgraph.graph import END, START, StateGraph
    from pydantic import SecretStr

    from application.graphs.state import GraphState

    llm = ChatOpenAI(api_key=SecretStr(api_key), model="gpt-4o-mini")

    async def chat_node(state: GraphState) -> dict:
        """Process messages through LLM."""
        response = await llm.ainvoke(state["messages"])
        return {"messages": [response]}

    graph = StateGraph(GraphState)
    graph.add_node("chat", chat_node)
    graph.add_edge(START, "chat")
    graph.add_edge("chat", END)
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
        "main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.debug,
    )
