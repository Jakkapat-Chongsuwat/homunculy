"""LINE channel client adapter."""

from __future__ import annotations

import httpx

from common.logger import get_logger
from domain.interfaces import ChannelClientPort, ChannelOutbound
from settings import line_settings

logger = get_logger(__name__)


class LineChannelClient(ChannelClientPort):
    """LINE adapter - sends outbound messages."""

    async def send(self, message: ChannelOutbound) -> None:
        """Send outbound message to LINE."""
        if not _enabled():
            return _log_skip(message)
        await _deliver(message)


def _enabled() -> bool:
    """Check if LINE credentials are configured."""
    return bool(line_settings.channel_access_token)


def _log_skip(message: ChannelOutbound) -> None:
    """Log skip when LINE is not configured."""
    logger.warning("LINE disabled", tenant_id=message.tenant_id, user_id=message.user_id)


async def _deliver(message: ChannelOutbound) -> None:
    """Deliver message via reply or push."""
    token = _reply_token(message)
    if token:
        return await _reply_message(message, token)
    await _push_message(message)


def _reply_token(message: ChannelOutbound) -> str:
    """Extract reply token from metadata."""
    return str(message.metadata.get("reply_token", ""))


async def _reply_message(message: ChannelOutbound, token: str) -> None:
    """Reply using LINE reply API."""
    url = f"{line_settings.api_base}/v2/bot/message/reply"
    payload = _reply_payload(token, message.text)
    await _post(url, payload)


async def _push_message(message: ChannelOutbound) -> None:
    """Push message using LINE Messaging API."""
    url = f"{line_settings.api_base}/v2/bot/message/push"
    payload = _push_payload(message)
    await _post(url, payload)


def _push_payload(message: ChannelOutbound) -> dict:
    """Build LINE push payload."""
    return {"to": message.user_id, "messages": [{"type": "text", "text": message.text}]}


def _reply_payload(token: str, text: str) -> dict:
    """Build LINE reply payload."""
    return {"replyToken": token, "messages": [{"type": "text", "text": text}]}


def _headers() -> dict:
    """Build LINE request headers."""
    return {"Authorization": f"Bearer {line_settings.channel_access_token}"}


async def _post(url: str, payload: dict) -> None:
    """POST payload to LINE API."""
    headers = _headers()
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(url, json=payload, headers=headers)
        if resp.is_error:
            logger.error("LINE send failed", status=resp.status_code, body=resp.text)
