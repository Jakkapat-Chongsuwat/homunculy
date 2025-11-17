"""
Homunculy - AI Agent Management System.

Main application entry point for the FastAPI server.
Following Clean Architecture principles with clear separation of concerns.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from internal.adapters.http import agent_handler
from internal.infrastructure.persistence.sqlalchemy import init_db, close_db
from settings import APP_NAME, APP_VERSION


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    print(f"Starting {APP_NAME} v{APP_VERSION}")
    # Initialize database
    await init_db()
    print("Database initialized")
    yield
    # Cleanup
    await close_db()
    print(f"Shutting down {APP_NAME}")


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    lifespan=lifespan,
    description="AI Agent Management System following Clean Architecture"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(agent_handler.router)


@app.exception_handler(Exception)
async def universal_exception_handler(_, exc):
    return JSONResponse(
        content={'error': f'{type(exc).__name__}: {exc}'},
        status_code=500
    )


@app.get('/', include_in_schema=False)
async def root():
    return JSONResponse({
        'service': APP_NAME,
        'version': APP_VERSION,
        'status': 'running'
    })


@app.get('/health', include_in_schema=False)
async def health_check():
    return JSONResponse({
        'status': 'healthy',
        'service': APP_NAME,
        'version': APP_VERSION
    })
