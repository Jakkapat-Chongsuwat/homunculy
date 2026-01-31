"""Channel entities for inbound/outbound routing."""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ChannelAccount(BaseModel):
    """External channel account mapping."""

    id: str
    tenant_id: str
    channel: str
    external_id: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChannelMessage(BaseModel):
    """Inbound channel message."""

    id: str
    tenant_id: str
    channel: str
    user_id: str
    text: str
    created_at: datetime = Field(default_factory=_now)
    metadata: dict[str, Any] = Field(default_factory=dict)
