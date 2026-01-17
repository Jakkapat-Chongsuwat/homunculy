"""FastAPI application factory."""

from contextlib import asynccontextmanager
from typing import Any

from common.logger import configure_logging, get_logger
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from presentation.http.routes import router

logger = get_logger(__name__)


def create_app(
    name: str = "homunculy",
    version: str = "1.0.0",
    on_startup: Any = None,
    on_shutdown: Any = None,
) -> FastAPI:
    """Create FastAPI application with configuration."""
    configure_logging()

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        logger.info("Application starting", app=name, version=version)
        if on_startup:
            await on_startup()
        yield
        if on_shutdown:
            await on_shutdown()
        logger.info("Application shutting down", app=name)

    app = FastAPI(
        title=name,
        version=version,
        lifespan=lifespan,
        description="AI Agent Management System",
    )

    _add_middleware(app)
    _add_routes(app)
    _add_exception_handlers(app)

    return app


def _add_middleware(app: FastAPI) -> None:
    """Add middleware to application."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def _add_routes(app: FastAPI) -> None:
    """Add routes to application."""
    app.include_router(router)
    app.add_api_route("/", _root, methods=["GET"], include_in_schema=False)
    app.add_api_route("/health", _health, methods=["GET"], include_in_schema=False)


def _add_exception_handlers(app: FastAPI) -> None:
    """Add exception handlers."""
    app.add_exception_handler(Exception, _exception_handler)


async def _root() -> JSONResponse:
    """Root endpoint."""
    return JSONResponse({"service": "homunculy", "status": "running"})


async def _health() -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse({"status": "healthy"})


async def _exception_handler(_, exc: Exception) -> JSONResponse:
    """Global exception handler."""
    logger.error("Unhandled exception", error=str(exc), exc_info=True)
    return JSONResponse(
        content={"error": f"{type(exc).__name__}: {exc}"},
        status_code=500,
    )
