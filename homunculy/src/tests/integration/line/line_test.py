"""LINE Integration Tests.

Tests the full LINE webhook flow:
1. LINE Webhook signature validation
2. Gateway routing (session + tenant policy)
3. Dual-System orchestration (mocked LLM)
4. LINE Reply API (via WireMock)

Fixtures use DI container overrides to mock LLM while testing real:
- HTTP layer (FastAPI)
- Database (PostgreSQL testcontainer)
- LINE API (WireMock testcontainer)
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time

import httpx
import pytest
import pytest_asyncio
from dependency_injector import providers
from httpx import ASGITransport, AsyncClient
from testcontainers.core.container import DockerContainer
from testcontainers.postgres import PostgresContainer

from domain.interfaces import (
    ChannelOutbound,
    DualSystemInput,
    DualSystemOutput,
    DualSystemPort,
    EmotionalTone,
    ResponseType,
)

# =============================================================================
# Constants
# =============================================================================

TEST_LINE_SECRET = "test-secret-line-integration"
TEST_LINE_TOKEN = "test-token-line-integration"
MOCK_RESPONSE = "Hello! I'm your friendly companion."


# =============================================================================
# Mock Dual-System (replaces LLM)
# =============================================================================


class MockDualSystem(DualSystemPort):
    """Mock dual-system that returns canned responses."""

    async def process(self, input_: DualSystemInput) -> DualSystemOutput:
        """Return mock response without LLM."""
        return DualSystemOutput(
            text=MOCK_RESPONSE,
            response_type=ResponseType.COGNITION,
            reflex=None,
            cognition=None,
            emotion=EmotionalTone.NEUTRAL,
        )

    async def stream(self, input_: DualSystemInput):
        """Stream mock response."""
        yield DualSystemOutput(
            text=MOCK_RESPONSE,
            response_type=ResponseType.COGNITION,
            reflex=None,
            cognition=None,
            emotion=EmotionalTone.NEUTRAL,
        )

    async def interrupt(self, session_id: str) -> None:
        """No-op interrupt for mock."""
        pass


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(scope="function")
def wiremock():
    """Start WireMock container for LINE API stubs."""
    container = DockerContainer("wiremock/wiremock:3.9.1").with_exposed_ports(8080)
    try:
        container.start()
        host = container.get_container_host_ip()
        port = container.get_exposed_port(8080)
        base_url = f"http://{host}:{port}"
        _stub_line_api(base_url)
        yield base_url
    except Exception as exc:
        pytest.skip(f"WireMock unavailable: {exc}")
    finally:
        container.stop()


@pytest_asyncio.fixture
async def app_client(
    postgres_container: PostgresContainer,
    wiremock: str,
    monkeypatch,
):
    """Create async client with mocked LLM and real containers."""
    # 1. Database env vars
    _set_db_env(postgres_container, monkeypatch)

    # 2. LINE env vars
    monkeypatch.setenv("LINE_CHANNEL_SECRET", TEST_LINE_SECRET)
    monkeypatch.setenv("LINE_CHANNEL_ACCESS_TOKEN", TEST_LINE_TOKEN)
    monkeypatch.setenv("LINE_API_BASE", wiremock)

    # 3. Gateway env vars
    monkeypatch.setenv("GATEWAY_REDIS_EMBEDDED", "true")

    # 4. Reload LINE settings
    from settings import line as line_module

    line_module.line_settings = line_module.LineSettings()

    # 5. Override DI container to use MockDualSystem
    from infrastructure.container import container

    mock_dual_system = MockDualSystem()
    container.dual_system.override(providers.Object(mock_dual_system))

    try:
        # 6. Create app
        from main import create_api

        app = create_api()

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            yield client
    finally:
        # 7. Always reset container overrides
        container.dual_system.reset_override()


# =============================================================================
# Helpers
# =============================================================================


def _set_db_env(postgres_container: PostgresContainer, monkeypatch) -> None:
    """Set database environment variables from container."""
    conn_url = postgres_container.get_connection_url()
    parts = conn_url.replace("postgresql+psycopg2://", "").split("@")
    user_pass = parts[0].split(":")
    host_port_db = parts[1].split("/")
    host_port = host_port_db[0].split(":")

    monkeypatch.setenv("DB_HOST", host_port[0])
    monkeypatch.setenv("DB_PORT", host_port[1])
    monkeypatch.setenv("DB_NAME", host_port_db[1])
    monkeypatch.setenv("DB_USER", user_pass[0])
    monkeypatch.setenv("DB_PASSWORD", user_pass[1])


def _stub_line_api(base_url: str) -> None:
    """Configure WireMock to stub LINE API endpoints."""
    mappings = [
        {"urlPattern": "/v2/bot/message/reply", "status": 200},
        {"urlPattern": "/v2/bot/message/push", "status": 200},
    ]
    for m in mappings:
        _post_stub(base_url, m["urlPattern"], m["status"])


def _post_stub(base_url: str, url_pattern: str, status: int) -> None:
    """Register a WireMock stub."""
    payload = {
        "request": {"method": "POST", "urlPattern": url_pattern},
        "response": {"status": status, "jsonBody": {"ok": True}},
    }
    _post_with_retry(f"{base_url}/__admin/mappings", payload)


def _post_with_retry(url: str, payload: dict) -> None:
    """POST to WireMock with retry for startup lag."""
    for _ in range(5):
        try:
            httpx.post(url, json=payload, timeout=5.0)
            return
        except Exception:
            time.sleep(1)
    raise RuntimeError("WireMock did not start in time")


def _compute_signature(secret: str, body: bytes) -> str:
    """Compute LINE webhook signature."""
    mac = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).digest()
    return base64.b64encode(mac).decode("utf-8")


async def _get_wiremock_requests(base_url: str) -> list[dict]:
    """Get all requests received by WireMock."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(f"{base_url}/__admin/requests")
        return json.loads(resp.text).get("requests", [])


async def _clear_wiremock_requests(base_url: str) -> None:
    """Clear WireMock request journal."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        await client.delete(f"{base_url}/__admin/requests")


def _line_event(text: str, reply_token: str = "reply-token-1") -> dict:
    """Build a LINE text message event."""
    return {
        "type": "message",
        "eventId": "evt-123",
        "timestamp": 1234567890,
        "replyToken": reply_token,
        "message": {"type": "text", "text": text},
        "source": {"type": "user", "userId": "user-integration-test"},
    }


async def _post_webhook(client: AsyncClient, events: list[dict]) -> httpx.Response:
    """POST events to LINE webhook endpoint."""
    payload = {"events": events}
    body = json.dumps(payload).encode("utf-8")
    signature = _compute_signature(TEST_LINE_SECRET, body)
    return await client.post(
        "/api/v1/channels/line/webhook",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Line-Signature": signature,
        },
    )


# =============================================================================
# Tests - Webhook Signature
# =============================================================================


class TestLineWebhookSignature:
    """LINE webhook signature validation tests."""

    @pytest.mark.asyncio
    async def test_valid_signature_accepted(self, app_client: AsyncClient):
        """Webhook accepts valid signature."""
        response = await _post_webhook(app_client, [_line_event("Hello")])
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_invalid_signature_rejected(self, app_client: AsyncClient):
        """Webhook rejects invalid signature."""
        body = json.dumps({"events": [_line_event("Hello")]}).encode("utf-8")
        response = await app_client.post(
            "/api/v1/channels/line/webhook",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-Line-Signature": "invalid-signature",
            },
        )
        assert response.status_code == 401


# =============================================================================
# Tests - Webhook Event Handling
# =============================================================================


class TestLineWebhookEvents:
    """LINE webhook event handling tests."""

    @pytest.mark.asyncio
    async def test_text_event_handled(self, app_client: AsyncClient):
        """Text message events are handled."""
        response = await _post_webhook(app_client, [_line_event("Hi there!")])
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["handled"] == 1

    @pytest.mark.asyncio
    async def test_multiple_events_handled(self, app_client: AsyncClient):
        """Multiple events in one payload are all handled."""
        events = [
            _line_event("First message", "token-1"),
            _line_event("Second message", "token-2"),
        ]
        response = await _post_webhook(app_client, events)
        assert response.status_code == 200
        assert response.json()["handled"] == 2

    @pytest.mark.asyncio
    async def test_non_text_events_ignored(self, app_client: AsyncClient):
        """Non-text events (stickers, images) are ignored."""
        event = {
            "type": "message",
            "eventId": "evt-sticker",
            "timestamp": 123,
            "replyToken": "token-sticker",
            "message": {"type": "sticker", "stickerId": "123"},
            "source": {"type": "user", "userId": "user-1"},
        }
        response = await _post_webhook(app_client, [event])
        assert response.status_code == 200
        assert response.json()["handled"] == 0


# =============================================================================
# Tests - Full Flow (Webhook → Gateway → Dual-System → Reply)
# =============================================================================


class TestLineFullFlow:
    """Full LINE integration flow tests."""

    @pytest.mark.asyncio
    async def test_message_flow_sends_reply(
        self,
        app_client: AsyncClient,
        wiremock: str,
    ):
        """Message triggers reply to LINE API."""
        await _clear_wiremock_requests(wiremock)

        response = await _post_webhook(app_client, [_line_event("Who are you?")])
        assert response.status_code == 200

        # Give async processing time to complete
        import asyncio

        await asyncio.sleep(0.5)

        requests = await _get_wiremock_requests(wiremock)
        reply_requests = [r for r in requests if "/reply" in r["request"]["url"]]
        assert len(reply_requests) >= 1, "No reply sent to LINE"

    @pytest.mark.asyncio
    async def test_reply_contains_mock_response(
        self,
        app_client: AsyncClient,
        wiremock: str,
    ):
        """Reply message contains the mocked dual-system response."""
        await _clear_wiremock_requests(wiremock)

        await _post_webhook(app_client, [_line_event("Hello!")])

        requests = await _get_wiremock_requests(wiremock)
        reply_requests = [r for r in requests if "/reply" in r["request"]["url"]]
        assert len(reply_requests) >= 1

        body = json.loads(reply_requests[-1]["request"]["body"])
        messages = body.get("messages", [])
        assert len(messages) > 0
        assert messages[0]["text"] == MOCK_RESPONSE

    @pytest.mark.asyncio
    async def test_no_internal_leak_in_reply(
        self,
        app_client: AsyncClient,
        wiremock: str,
    ):
        """Reply does not leak internal messages (supervisor/handoff)."""
        await _clear_wiremock_requests(wiremock)

        await _post_webhook(app_client, [_line_event("Tell me something")])

        requests = await _get_wiremock_requests(wiremock)
        reply_requests = [r for r in requests if "/reply" in r["request"]["url"]]

        for req in reply_requests:
            body = json.loads(req["request"]["body"])
            for msg in body.get("messages", []):
                text = msg.get("text", "").lower()
                assert "supervisor" not in text, "Supervisor leaked"
                assert "transferring" not in text, "Handoff leaked"


# =============================================================================
# Tests - LINE Client (Outbound)
# =============================================================================


class TestLineOutbound:
    """LINE outbound client tests."""

    @pytest.mark.asyncio
    async def test_reply_uses_reply_endpoint(self, wiremock: str, monkeypatch):
        """Reply message uses /v2/bot/message/reply endpoint."""
        await _clear_wiremock_requests(wiremock)

        monkeypatch.setenv("LINE_API_BASE", wiremock)
        monkeypatch.setenv("LINE_CHANNEL_ACCESS_TOKEN", TEST_LINE_TOKEN)

        # Reload LINE settings after setting env vars
        from settings import line as line_module

        line_module.line_settings = line_module.LineSettings()

        from infrastructure.adapters.channels.line_client import LineChannelClient
        from infrastructure.adapters.gateway.token_provider import ConfigTokenProvider

        client = LineChannelClient(ConfigTokenProvider())
        await client.send(_reply_outbound())

        requests = await _get_wiremock_requests(wiremock)
        paths = [r["request"]["url"] for r in requests]
        assert "/v2/bot/message/reply" in paths

    @pytest.mark.asyncio
    async def test_push_uses_push_endpoint(self, wiremock: str, monkeypatch):
        """Push message uses /v2/bot/message/push endpoint."""
        await _clear_wiremock_requests(wiremock)

        monkeypatch.setenv("LINE_API_BASE", wiremock)
        monkeypatch.setenv("LINE_CHANNEL_ACCESS_TOKEN", TEST_LINE_TOKEN)

        # Reload LINE settings after setting env vars
        from settings import line as line_module

        line_module.line_settings = line_module.LineSettings()

        from infrastructure.adapters.channels.line_client import LineChannelClient
        from infrastructure.adapters.gateway.token_provider import ConfigTokenProvider

        client = LineChannelClient(ConfigTokenProvider())
        await client.send(_push_outbound())

        requests = await _get_wiremock_requests(wiremock)
        paths = [r["request"]["url"] for r in requests]
        assert "/v2/bot/message/push" in paths


def _reply_outbound() -> ChannelOutbound:
    """Build outbound message with reply token."""
    return ChannelOutbound(
        tenant_id="t1",
        channel="line",
        user_id="u1",
        text="Hello from test",
        metadata={"reply_token": "token-reply-test"},
    )


def _push_outbound() -> ChannelOutbound:
    """Build outbound push message (no reply token)."""
    return ChannelOutbound(
        tenant_id="t1",
        channel="line",
        user_id="u1",
        text="Hello push",
        metadata={},
    )
