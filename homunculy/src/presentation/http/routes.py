"""HTTP routes definition."""

from fastapi import APIRouter

from presentation.http.handlers.agent import router as agent_router
from presentation.http.handlers.line_webhook import router as line_router

router = APIRouter()

# Include sub-routers
router.include_router(agent_router, prefix="/api/v1/agents", tags=["Agents"])
router.include_router(line_router, prefix="/api/v1/channels", tags=["Channels"])
