"""LiveKit JWT token generation for WebRTC room access."""

import time

import jwt

from common.logger import get_logger

logger = get_logger(__name__)


def create_room_token(
    api_key: str,
    api_secret: str,
    room: str,
    identity: str,
    ttl: int = 3600,
) -> str:
    """Create JWT token for LiveKit room access."""
    claims = _build_claims(api_key, room, identity, ttl)
    return _sign_token(claims, api_key, api_secret)


def _build_claims(api_key: str, room: str, identity: str, ttl: int) -> dict:
    """Build JWT claims for room access."""
    now = int(time.time())
    return {
        "exp": now + ttl,
        "iss": api_key,
        "sub": identity,
        "video": _video_grants(room),
    }


def _video_grants(room: str) -> dict:
    """Build video grants for room."""
    return {
        "room": room,
        "roomJoin": True,
        "canPublish": True,
        "canSubscribe": True,
        "canPublishData": True,
    }


def _sign_token(claims: dict, api_key: str, api_secret: str) -> str:
    """Sign JWT with API credentials."""
    headers = {"kid": api_key}
    return jwt.encode(claims, api_secret, algorithm="HS256", headers=headers)
