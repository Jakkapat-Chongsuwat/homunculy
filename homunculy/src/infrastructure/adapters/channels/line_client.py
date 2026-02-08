"""LINE channel client adapter."""

from __future__ import annotations

import httpx

from common.logger import get_logger
from domain.interfaces import ChannelClientPort, ChannelOutbound, ChannelTokenProviderPort
from settings import line

logger = get_logger(__name__)


class LineChannelClient(ChannelClientPort):
    """LINE adapter - sends outbound messages."""

    def __init__(self, tokens: ChannelTokenProviderPort) -> None:
        self._tokens = tokens

    async def send(self, message: ChannelOutbound) -> None:
        """Send outbound message to LINE."""
        token = self._token(message)
        if not token:
            return _log_skip(message)
        logger.debug("LINE send", channel=message.channel, user_id=message.user_id)
        await _deliver(message, token)

    def _token(self, message: ChannelOutbound) -> str | None:
        """Resolve token for message."""
        token = self._tokens.get_token(message.tenant_id, message.channel, message.user_id)
        return token or line.line_settings.channel_access_token


def _enabled() -> bool:
    """Check if LINE credentials are configured."""
    return bool(line.line_settings.channel_access_token)


def _log_skip(message: ChannelOutbound) -> None:
    """Log skip when LINE is not configured."""
    logger.warning("LINE disabled", tenant_id=message.tenant_id, user_id=message.user_id)


async def _deliver(message: ChannelOutbound, access_token: str) -> None:
    """Deliver message via reply or push."""
    reply_token = _reply_token(message)
    if reply_token:
        logger.debug("LINE reply", user_id=message.user_id)
        return await _reply_message(message, access_token, reply_token)
    logger.debug("LINE push", user_id=message.user_id)
    await _push_message(message, access_token)


def _reply_token(message: ChannelOutbound) -> str:
    """Extract reply token from metadata."""
    return str(message.metadata.get("reply_token", ""))


async def _reply_message(message: ChannelOutbound, access_token: str, reply_token: str) -> None:
    """Reply using LINE reply API."""
    url = f"{line.line_settings.api_base}/v2/bot/message/reply"
    payload = _reply_payload(reply_token, message.text)
    await _post(url, payload, access_token)


async def _push_message(message: ChannelOutbound, token: str) -> None:
    """Push message using LINE Messaging API."""
    url = f"{line.line_settings.api_base}/v2/bot/message/push"
    payload = _push_payload(message)
    await _post(url, payload, token)


def _push_payload(message: ChannelOutbound) -> dict:
    """Build LINE push payload."""
    return {"to": message.user_id, "messages": [{"type": "text", "text": message.text}]}


def _reply_payload(token: str, text: str) -> dict:
    """Build LINE reply payload."""
    return {"replyToken": token, "messages": [{"type": "text", "text": text}]}


def _headers(token: str) -> dict:
    """Build LINE request headers."""
    return {"Authorization": f"Bearer {token}"}


async def _post(url: str, payload: dict, token: str) -> None:
    """POST payload to LINE API."""
    headers = _headers(token)
    logger.debug("LINE request", url=url, payload=payload)
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(url, json=payload, headers=headers)
        if resp.is_error:
            logger.error("LINE send failed", status=resp.status_code, body=resp.text)
        else:
            logger.debug("LINE send ok", status=resp.status_code)
