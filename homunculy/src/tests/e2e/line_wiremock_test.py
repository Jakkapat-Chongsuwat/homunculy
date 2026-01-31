"""E2E tests for LINE outbound with WireMock Testcontainer."""

from __future__ import annotations

import json
import time

import httpx
import pytest
from testcontainers.core.container import DockerContainer

from domain.interfaces import ChannelOutbound
from infrastructure.adapters.channels.line_client import LineChannelClient
from settings import line_settings


@pytest.fixture(scope="module")
def wiremock():
    container = DockerContainer("wiremock/wiremock:3.9.1").with_exposed_ports(8080)
    try:
        container.start()
        host = container.get_container_host_ip()
        port = container.get_exposed_port(8080)
        base_url = f"http://{host}:{port}"
        _stub_wiremock(base_url)
        yield base_url
    except Exception as exc:
        pytest.skip(f"WireMock unavailable: {exc}")
    finally:
        container.stop()


@pytest.mark.asyncio
async def test_line_reply_and_push(wiremock, monkeypatch):
    monkeypatch.setattr(line_settings, "api_base", wiremock)
    monkeypatch.setattr(line_settings, "channel_access_token", "test-token")

    client = LineChannelClient()
    await client.send(_reply_message())
    await client.send(_push_message())

    data = await _requests(wiremock)
    paths = [r["request"]["url"] for r in data]
    assert "/v2/bot/message/reply" in paths
    assert "/v2/bot/message/push" in paths


def _reply_message() -> ChannelOutbound:
    return ChannelOutbound(
        tenant_id="t1",
        channel="line",
        user_id="u1",
        text="hello",
        metadata={"reply_token": "token-1"},
    )


def _push_message() -> ChannelOutbound:
    return ChannelOutbound(
        tenant_id="t1",
        channel="line",
        user_id="u1",
        text="hello",
        metadata={},
    )


def _stub_wiremock(base_url: str) -> None:
    payload = {
        "request": {"method": "POST", "urlPattern": "/v2/bot/message/.*"},
        "response": {"status": 200, "jsonBody": {"ok": True}},
    }
    _post_with_retry(f"{base_url}/__admin/mappings", payload)


def _post_with_retry(url: str, payload: dict) -> None:
    for _ in range(5):
        try:
            httpx.post(url, json=payload, timeout=5.0)
            return
        except Exception:
            time.sleep(1)
    raise RuntimeError("WireMock did not start in time")


async def _requests(base_url: str) -> list[dict]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(f"{base_url}/__admin/requests")
        return json.loads(resp.text).get("requests", [])
