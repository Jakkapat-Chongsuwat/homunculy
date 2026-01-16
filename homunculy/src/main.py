"""
Homunculy - AI Agent Management System.

Main application entry point for the FastAPI server.
Following Clean Architecture principles with clear separation of concerns.
"""

from contextlib import asynccontextmanager

from common.logger import configure_logging, get_logger
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from internal.adapters.http import agent_router, livekit_router
from internal.infrastructure.container import get_llm_service, get_tts_service
from internal.infrastructure.persistence.sqlalchemy import close_db, init_db
from settings import APP_NAME, APP_VERSION
from starlette.middleware.cors import CORSMiddleware

# Configure structured logging on startup
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager (Go-style dependency wiring).

    Like Go's main() function, this is where we:
    1. Initialize infrastructure (database, external services)
    2. Wire up dependencies
    3. Validate service availability
    4. Clean up on shutdown
    """
    logger.info("Application starting", app=APP_NAME, version=APP_VERSION)

    # Initialize database connection pool
    await init_db()
    logger.info("Database initialized")

    # Wire up services (like Go's dependency injection in main)
    # This validates TTS availability at startup
    tts_service = get_tts_service()
    if tts_service:
        logger.info("TTS service available (ElevenLabs)")
    else:
        logger.warning("TTS service not configured - agents won't have TTS tools")

    # Validate LLM service can be constructed
    try:
        _ = get_llm_service()
        logger.info("LLM service initialized", provider="LangGraph")
    except Exception as e:
        logger.error("Failed to initialize LLM service", error=str(e))
        raise

    yield

    # Cleanup (like Go's defer)
    await close_db()
    logger.info("Application shutting down", app=APP_NAME)


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    lifespan=lifespan,
    description="AI Agent Management System following Clean Architecture",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register HTTP routes
app.include_router(agent_router)

# LiveKit: WebRTC token issuance for clients
app.include_router(livekit_router)


@app.exception_handler(Exception)
async def universal_exception_handler(_, exc):
    return JSONResponse(content={"error": f"{type(exc).__name__}: {exc}"}, status_code=500)


@app.get("/", include_in_schema=False)
async def root():
    return JSONResponse({"service": APP_NAME, "version": APP_VERSION, "status": "running"})


@app.get("/health", include_in_schema=False)
async def health_check():
    return JSONResponse({"status": "healthy", "service": APP_NAME, "version": APP_VERSION})
