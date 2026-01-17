"""LiveKit HTTP handler."""

from common.logger import get_logger
from fastapi import APIRouter
from infrastructure.livekit import create_room_token
from pydantic import BaseModel

logger = get_logger(__name__)
router = APIRouter()

# Settings placeholder
_api_key = ""
_api_secret = ""


def configure_livekit(api_key: str, api_secret: str) -> None:
    """Configure LiveKit credentials."""
    global _api_key, _api_secret
    _api_key = api_key
    _api_secret = api_secret


class TokenRequest(BaseModel):
    """Token request DTO."""

    room: str
    identity: str
    ttl: int = 3600


class TokenResponse(BaseModel):
    """Token response DTO."""

    token: str
    room: str
    identity: str


@router.post("/token", response_model=TokenResponse)
async def get_token(request: TokenRequest) -> TokenResponse:
    """Generate LiveKit room token."""
    logger.info("Generating token", room=request.room, identity=request.identity)
    token = create_room_token(
        api_key=_api_key,
        api_secret=_api_secret,
        room=request.room,
        identity=request.identity,
        ttl=request.ttl,
    )
    return TokenResponse(
        token=token,
        room=request.room,
        identity=request.identity,
    )
