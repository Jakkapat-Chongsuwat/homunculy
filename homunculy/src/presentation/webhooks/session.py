"""Session event webhooks."""

from common.logger import get_logger
from fastapi import APIRouter, Request
from pydantic import BaseModel

logger = get_logger(__name__)
router = APIRouter()


class SessionEvent(BaseModel):
    """Session event DTO."""

    event_type: str
    session_id: str
    room_name: str
    participant_identity: str
    timestamp: int


@router.post("/session/start")
async def on_session_start(event: SessionEvent) -> dict:
    """Handle session start event."""
    logger.info(
        "Session started",
        session_id=event.session_id,
        room=event.room_name,
        participant=event.participant_identity,
    )
    return {"status": "acknowledged", "event": "session_start"}


@router.post("/session/end")
async def on_session_end(event: SessionEvent) -> dict:
    """Handle session end event."""
    logger.info(
        "Session ended",
        session_id=event.session_id,
        room=event.room_name,
    )
    return {"status": "acknowledged", "event": "session_end"}


@router.post("/livekit/webhook")
async def livekit_webhook(request: Request) -> dict:
    """Handle LiveKit server webhook."""
    body = await request.json()
    event_type = body.get("event", "unknown")
    logger.info("LiveKit webhook received", event_type=event_type)
    return {"status": "ok", "event": event_type}
