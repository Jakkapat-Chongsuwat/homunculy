"""LiveKit E2E: dispatch + chat via text data."""

from __future__ import annotations

import asyncio
import os
import socket
import time
from pathlib import Path
from typing import Any

import pytest
from testcontainers.core.container import DockerContainer

livekit = pytest.importorskip("livekit")
from livekit import api, rtc  # type: ignore  # noqa: E402

LIVEKIT_IMAGE = "livekit/livekit-server:v1.9.11"
LIVEKIT_KEY = "devkey"
LIVEKIT_SECRET = "devsecretdevsecretdevsecretdevsecret"
TOPIC_CHAT = "lk-chat"
AGENT_NAME = "homunculy-super"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _config_path() -> str:
    return str(_repo_root() / "infra" / "livekit" / "livekit.yaml")


def _ws_url(port: str) -> str:
    return f"ws://localhost:{port}"


def _http_url(port: str) -> str:
    return f"http://localhost:{port}"


def _token(room: str, identity: str, dispatch: bool) -> str:
    grants = api.VideoGrants(room_join=True, room=room, can_publish_data=True)
    builder = api.AccessToken(api_key=LIVEKIT_KEY, api_secret=LIVEKIT_SECRET)
    builder = builder.with_identity(identity).with_grants(grants)
    if not dispatch:
        return builder.to_jwt()
    config = api.RoomConfiguration(
        agents=[api.RoomAgentDispatch(agent_name=AGENT_NAME, metadata='{"e2e":true}')]
    )
    return builder.with_room_config(config).to_jwt()


def _text_future() -> asyncio.Future[tuple[str, str]]:
    return asyncio.get_running_loop().create_future()


def _register_text(room: rtc.Room, future: asyncio.Future[tuple[str, str]]) -> None:
    def handler(reader: rtc.TextStreamReader, identity: str) -> None:
        async def read() -> None:
            text = await reader.read_all()
            if not future.done():
                future.set_result((text, identity))

        asyncio.create_task(read())

    room.register_text_stream_handler(TOPIC_CHAT, handler)


def _start_container() -> DockerContainer:
    os.environ.setdefault("TESTCONTAINERS_RYUK_DISABLED", "true")
    container = DockerContainer(LIVEKIT_IMAGE)
    container.with_volume_mapping(_config_path(), "/livekit.yaml")
    container.with_command("--config /livekit.yaml")
    return container.with_exposed_ports(7880)


def _exposed_port(container: DockerContainer, port: int) -> str:
    for _ in range(20):
        try:
            return str(container.get_exposed_port(port))
        except Exception:
            time.sleep(0.5)
    pytest.skip("LiveKit port mapping not available")


def _wait_livekit(host: str, port: int) -> None:
    for _ in range(20):
        try:
            with socket.create_connection((host, port), timeout=1):
                return
        except Exception:
            time.sleep(0.5)
    pytest.skip("LiveKit not ready")


@pytest.fixture(scope="session")
def livekit_container() -> Any:
    container = _start_container()
    container.start()
    yield container
    container.stop()


@pytest.fixture(scope="session")
def livekit_urls(livekit_container: Any) -> dict[str, str]:
    port_str = _exposed_port(livekit_container, 7880)
    port = int(port_str)
    urls = {"ws": _ws_url(port_str), "http": _http_url(port_str)}
    _wait_livekit("localhost", port)
    return urls


async def _connect_room(url: str, token: str) -> rtc.Room:
    room = rtc.Room()
    await room.connect(url, token, rtc.RoomOptions(auto_subscribe=True))
    return room


async def _send_text(room: rtc.Room, text: str, target: str) -> None:
    await room.local_participant.send_text(
        text=text,
        topic=TOPIC_CHAT,
        destination_identities=[target],
    )


@pytest.mark.asyncio
async def test_livekit_dispatch_and_chat(livekit_urls: dict[str, str]) -> None:
    room_name = "e2e-livekit-dispatch"
    user_token = _token(room_name, "user-1", dispatch=True)
    agent_token = _token(room_name, "agent-1", dispatch=False)

    agent_room = await _connect_room(livekit_urls["ws"], agent_token)
    user_room = await _connect_room(livekit_urls["ws"], user_token)

    agent_future = _text_future()
    user_future = _text_future()
    _register_text(agent_room, agent_future)
    _register_text(user_room, user_future)

    await _send_text(user_room, "hello agent", "agent-1")
    msg, sender = await asyncio.wait_for(agent_future, timeout=10)
    assert msg == "hello agent"
    assert sender == "user-1"

    await _send_text(agent_room, "hello user", "user-1")
    reply, sender = await asyncio.wait_for(user_future, timeout=10)
    assert reply == "hello user"
    assert sender == "agent-1"

    await user_room.disconnect()
    await agent_room.disconnect()
