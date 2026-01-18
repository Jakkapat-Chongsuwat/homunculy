"""LiveKit Agent Service - Agent Controls Itself.

The agent is a STANDALONE SERVICE that receives commands from Control Plane.
Agent decides when to join rooms. LiveKit is just a media router.

Architecture:
1. Agent runs as HTTP service (FastAPI)
2. Management Service calls POST /join with room details
3. Agent creates its own token and connects to LiveKit
4. Agent is ACTIVE, not PASSIVE
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel

from common.logger import get_logger
from infrastructure.transport.session_handle import SessionRegistry

logger = get_logger(__name__)

# Config
AGENT_NAME = os.getenv("AGENT_NAME", "homunculy-super")

# Global session registry
_registry = SessionRegistry()


# --- API Models ---


class JoinRequest(BaseModel):
    """Request from Control Plane."""

    room: str
    user_id: str
    metadata: dict | None = None


class JoinResponse(BaseModel):
    """Response with session details."""

    session_id: str
    room: str
    status: str


class LeaveRequest(BaseModel):
    """Request to leave."""

    session_id: str


# --- Service Factory ---


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    logger.info("Agent service starting", agent=AGENT_NAME)
    yield
    await _registry.cleanup_all()
    logger.info("Agent service stopped")


def create_agent_service() -> FastAPI:
    """Create the agent HTTP service."""
    app = FastAPI(title=f"Agent: {AGENT_NAME}", lifespan=lifespan)
    _register_routes(app)
    return app


def _register_routes(app: FastAPI) -> None:
    """Register all routes."""
    app.get("/health")(_health)
    app.post("/join", response_model=JoinResponse)(_join)
    app.post("/leave")(_leave)
    app.get("/sessions")(_list_sessions)


# --- Route Handlers ---


async def _health():
    """Health check."""
    return {"status": "healthy", "agent": AGENT_NAME, "sessions": _registry.count}


async def _join(req: JoinRequest, background: BackgroundTasks):
    """Join a room."""
    handle = _registry.create(req.room, req.user_id, req.metadata or {})
    background.add_task(handle.run)
    return JoinResponse(session_id=handle.session_id, room=req.room, status="joining")


async def _leave(req: LeaveRequest):
    """Leave a room."""
    handle = _registry.remove(req.session_id)
    if not handle:
        raise HTTPException(404, "Session not found")
    await handle.stop()
    return {"status": "left", "session_id": req.session_id}


async def _list_sessions():
    """List active sessions."""
    return {"sessions": _registry.list_all()}


# --- Transport Adapter ---


class LiveKitWorker:
    """Transport adapter - runs agent as HTTP service."""

    def run(self) -> None:
        """Start agent service."""
        import uvicorn

        port = int(os.getenv("HEALTH_PORT", "8000"))
        uvicorn.run(create_agent_service(), host="0.0.0.0", port=port)


def create_worker() -> LiveKitWorker:
    """Factory for main.py."""
    return LiveKitWorker()
