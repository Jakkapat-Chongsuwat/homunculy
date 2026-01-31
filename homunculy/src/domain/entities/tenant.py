"""Tenant domain entity."""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Tenant(BaseModel):
    """Tenant model for multi-tenant routing."""

    id: str
    name: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=_now)
    metadata: dict[str, Any] = Field(default_factory=dict)
