"""E2E tests for LINE webhook routing."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import tempfile

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
def postgres_container():
    with PostgresContainer("postgres:16") as postgres:
        yield postgres


# Test secret for LINE signature verification
TEST_LINE_SECRET = "test-secret-for-line-webhook"


@pytest_asyncio.fixture
async def test_app(postgres_container: PostgresContainer, monkeypatch):
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
    monkeypatch.setenv("GATEWAY_REDIS_EMBEDDED", "true")
    monkeypatch.setenv("GATEWAY_REDIS_FILE", _redis_file())
    # Set LINE channel secret for signature validation
    monkeypatch.setenv("LINE_CHANNEL_SECRET", TEST_LINE_SECRET)

    from main import create_api

    app = create_api()
    yield app


def _redis_file() -> str:
    return f"{tempfile.mkdtemp()}/homunculy-redis.db"


def _compute_signature(secret: str, body: bytes) -> str:
    """Compute LINE signature header value."""
    mac = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).digest()
    return base64.b64encode(mac).decode("utf-8")


@pytest_asyncio.fixture
async def client(test_app):
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_line_webhook_accepts_text_event(client: AsyncClient):
    payload = {
        "events": [
            {
                "type": "message",
                "eventId": "evt-1",
                "timestamp": 1,
                "replyToken": "token-1",
                "message": {"type": "text", "text": "hi"},
                "source": {"type": "group", "groupId": "g1", "userId": "u1"},
            }
        ]
    }
    body = json.dumps(payload).encode("utf-8")
    signature = _compute_signature(TEST_LINE_SECRET, body)

    response = await client.post(
        "/api/v1/channels/line/webhook",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Line-Signature": signature,
        },
    )
    assert response.status_code == 200
    assert response.json()["handled"] == 1
