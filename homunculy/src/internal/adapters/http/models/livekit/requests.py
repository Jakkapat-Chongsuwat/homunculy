"""LiveKit request models."""

from pydantic import BaseModel, Field


class CreateJoinTokenRequest(BaseModel):
    tenant_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    identity: str = Field(default="")
    name: str = Field(default="")
    metadata: str = Field(default="")
    ttl_seconds: int = Field(default=3600, gt=0, le=24 * 3600)
