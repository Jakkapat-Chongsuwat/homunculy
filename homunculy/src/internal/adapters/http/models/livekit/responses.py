"""LiveKit response models."""

from pydantic import BaseModel


class CreateJoinTokenResponse(BaseModel):
    url: str
    room: str
    token: str
