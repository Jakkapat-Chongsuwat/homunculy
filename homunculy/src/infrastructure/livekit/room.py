"""LiveKit room management."""

from dataclasses import dataclass

from common.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RoomConfig:
    """LiveKit room configuration."""

    name: str
    max_participants: int = 10
    empty_timeout: int = 300
    metadata: str = ""


@dataclass
class RoomInfo:
    """LiveKit room information."""

    sid: str
    name: str
    num_participants: int
    creation_time: int


async def create_room(client, config: RoomConfig) -> RoomInfo:
    """Create a new LiveKit room."""
    logger.info("Creating room", name=config.name)
    response = await client.create_room(
        name=config.name,
        empty_timeout=config.empty_timeout,
        max_participants=config.max_participants,
        metadata=config.metadata,
    )
    return _to_room_info(response)


async def delete_room(client, name: str) -> None:
    """Delete a LiveKit room."""
    logger.info("Deleting room", name=name)
    await client.delete_room(name=name)


async def list_rooms(client) -> list[RoomInfo]:
    """List all active rooms."""
    response = await client.list_rooms()
    return [_to_room_info(r) for r in response.rooms]


def _to_room_info(room) -> RoomInfo:
    """Convert room response to RoomInfo."""
    return RoomInfo(
        sid=room.sid,
        name=room.name,
        num_participants=room.num_participants,
        creation_time=room.creation_time,
    )
