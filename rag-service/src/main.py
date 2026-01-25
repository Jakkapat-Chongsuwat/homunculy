"""
RAG Service - Retrieval-Augmented Generation with Pinecone.

Main application entry point for the FastAPI server.
Provides document ingestion pipeline and semantic search APIs.
"""

from contextlib import (
    asynccontextmanager,
)

from fastapi import (
    FastAPI,
)
from fastapi.responses import (
    JSONResponse,
)
from starlette.middleware.cors import (
    CORSMiddleware,
)

from internal.adapters.http import (
    ingest_router,
    query_router,
)
from internal.infrastructure.container import (
    get_vector_store_service,
)
from settings import (
    APP_NAME,
    APP_VERSION,
)
from settings.logging import (
    configure_logging,
    get_logger,
)
from settings.telemetry import (
    configure_opentelemetry,
)

configure_logging()
configure_opentelemetry()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(
    _app: FastAPI,
):
    """
    Application lifespan manager.

    Initializes:
    1. Vector store connection (Pinecone)
    2. Embedding service validation
    """
    logger.info(
        "RAG Service starting",
        app=APP_NAME,
        version=APP_VERSION,
    )

    # Validate vector store connection
    try:
        vector_store = get_vector_store_service()
        stats = await vector_store.get_index_stats()
        logger.info(
            "Vector store connected",
            index=stats.get("index_name"),
            vector_count=stats.get(
                "total_vector_count",
                0,
            ),
        )
    except Exception as e:
        logger.error(
            "Failed to connect to vector store",
            error=str(e),
        )
        raise

    yield

    # Cleanup
    logger.info(
        "RAG Service shutting down",
        app=APP_NAME,
    )


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    lifespan=lifespan,
    description="RAG Service - Document ingestion and semantic search with Pinecone",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(
    ingest_router,
    prefix="/api/v1",
    tags=["Ingestion"],
)
app.include_router(
    query_router,
    prefix="/api/v1",
    tags=["Query"],
)


@app.exception_handler(Exception)
async def universal_exception_handler(_, exc):
    """Global exception handler."""
    logger.error(
        "Unhandled exception",
        error=str(exc),
        exc_info=True,
    )
    return JSONResponse(
        content={"error": f"{type(exc).__name__}: {exc}"},
        status_code=500,
    )


@app.get(
    "/",
    include_in_schema=False,
)
async def root():
    """Root endpoint."""
    return JSONResponse(
        {
            "service": APP_NAME,
            "version": APP_VERSION,
            "status": "running",
        }
    )


@app.get(
    "/health",
    include_in_schema=False,
)
async def health_check():
    """Health check endpoint."""
    return JSONResponse(
        {
            "status": "healthy",
            "service": APP_NAME,
            "version": APP_VERSION,
        }
    )
