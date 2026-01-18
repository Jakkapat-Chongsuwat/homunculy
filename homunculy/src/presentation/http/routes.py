"""HTTP routes definition."""

from fastapi import APIRouter

from presentation.http.handlers.agent import router as agent_router

router = APIRouter()

# Include sub-routers
router.include_router(agent_router, prefix="/api/v1/agents", tags=["Agents"])
