"""LiveKit token service.

Stateless: derives room name from tenant/session and signs JWT.
"""

from __future__ import annotations

import os
import re
from datetime import timedelta

from livekit.api import AccessToken, VideoGrants


def create_join_token(
    *, tenant_id: str, session_id: str, identity: str, name: str, metadata: str, ttl: int
) -> tuple[str, str, str]:
    room = _room(tenant_id, session_id)
    token = _jwt(room, _identity(identity, tenant_id, session_id), _name(name), metadata, ttl)
    return _url(), room, token


def _url() -> str:
    return os.getenv("LIVEKIT_URL", "ws://localhost:7880")


def _jwt(room: str, identity: str, name: str, metadata: str, ttl: int) -> str:
    key, secret = _creds()
    grants = VideoGrants(
        room=room, room_join=True, can_publish=True, can_subscribe=True, can_publish_data=True
    )
    t = (
        AccessToken(key, secret)
        .with_identity(identity)
        .with_name(name)
        .with_grants(grants)
        .with_ttl(timedelta(seconds=ttl))
    )
    return t.with_metadata(metadata).to_jwt() if metadata else t.to_jwt()


def _creds() -> tuple[str, str]:
    return os.getenv("LIVEKIT_API_KEY", "devkey"), os.getenv("LIVEKIT_API_SECRET", "devsecret")


def _room(tenant_id: str, session_id: str) -> str:
    return _safe(f"t-{tenant_id}-s-{session_id}")


def _identity(identity: str, tenant_id: str, session_id: str) -> str:
    return identity or _safe(f"u-{tenant_id}-{session_id}")


def _name(name: str) -> str:
    return name or "Homunculy User"


def _safe(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]", "-", value)
    return cleaned[:64].strip("-") or "default"
