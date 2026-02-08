"""LINE webhook handler for channel routing."""

import base64
import hashlib
import hmac
import json

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from application.use_cases.gateway import RouteInboundInput, RouteInboundUseCase
from infrastructure.container import container
from settings import line

router = APIRouter()


class LineWebhookResponse(BaseModel):
    """LINE webhook response."""

    status: str
    handled: int


def get_gateway_use_case() -> RouteInboundUseCase:
    """DI provider for gateway use case."""
    return RouteInboundUseCase(
        orchestrator=container.gateway_orchestrator(),
        sessions=container.session_store(),
        policy=container.tenant_policy(),
        channel=container.channel_client(),
    )


@router.post("/line/webhook", response_model=LineWebhookResponse)
async def line_webhook(
    request: Request,
    use_case: RouteInboundUseCase = Depends(get_gateway_use_case),
) -> LineWebhookResponse:
    """Handle LINE webhook events."""
    body = await request.body()
    _verify_signature(request, body)
    payload = json.loads(body)
    tenant_id = _tenant_id(request)
    handled = await _handle_events(payload, tenant_id, use_case)
    return LineWebhookResponse(status="ok", handled=handled)


@router.get("/line/webhook", include_in_schema=False)
async def line_webhook_verify() -> LineWebhookResponse:
    """Handle webhook verification."""
    return LineWebhookResponse(status="ok", handled=0)


async def _handle_events(payload: dict, tenant_id: str, use_case: RouteInboundUseCase) -> int:
    """Handle LINE events payload."""
    handled = 0
    for event in _events(payload):
        handled += await _handle_event(event, tenant_id, use_case)
    return handled


async def _handle_event(event: dict, tenant_id: str, use_case: RouteInboundUseCase) -> int:
    """Handle a single LINE event."""
    if not _is_text_event(event):
        return 0
    await use_case.execute(_input(event, tenant_id))
    return 1


def _input(event: dict, tenant_id: str) -> RouteInboundInput:
    """Map LINE event to use-case input."""
    return RouteInboundInput(tenant_id, "line", _target_id(event), _text(event), _meta(event))


def _events(payload: dict) -> list[dict]:
    """Extract events list from payload."""
    return payload.get("events", [])


def _is_text_event(event: dict) -> bool:
    """Check if LINE event is a text message."""
    message = event.get("message", {})
    return event.get("type") == "message" and message.get("type") == "text"


def _text(event: dict) -> str:
    """Extract message text."""
    return event.get("message", {}).get("text", "")


def _user_id(event: dict) -> str:
    """Extract user id."""
    return _source(event).get("userId", "unknown")


def _meta(event: dict) -> dict:
    """Extract metadata from event."""
    return {
        "event_id": event.get("eventId"),
        "timestamp": event.get("timestamp"),
        "reply_token": _reply_token(event),
        "source_type": _source_type(event),
        "sender_id": _user_id(event),
        "target_id": _target_id(event),
    }


def _verify_signature(request: Request, body: bytes) -> None:
    """Verify LINE signature if secret is configured."""
    secret = _resolve_secret(request)
    if not secret:
        return
    header = request.headers.get("X-Line-Signature", "")
    expected = _signature(secret, body)
    if not hmac.compare_digest(header, expected):
        raise HTTPException(status_code=401, detail="Invalid signature")


def _signature(secret: str, body: bytes) -> str:
    """Compute LINE signature header value."""
    mac = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).digest()
    return base64.b64encode(mac).decode("utf-8")


def _resolve_secret(request: Request) -> str:
    """Resolve channel secret from token provider or settings."""
    tenant_id = _tenant_id(request)
    token_provider = container.token_provider()
    secret = token_provider.get_secret(tenant_id, "line", "default")
    return secret or line.line_settings.channel_secret


def _source(event: dict) -> dict:
    """Extract source object."""
    return event.get("source", {})


def _source_type(event: dict) -> str:
    """Extract source type."""
    return _source(event).get("type", "user")


def _target_id(event: dict) -> str:
    """Extract target id (user/group/room)."""
    return _target_by_type(_source(event), _source_type(event))


def _target_by_type(source: dict, source_type: str) -> str:
    """Map source type to target id."""
    if source_type == "group":
        return source.get("groupId", "unknown")
    if source_type == "room":
        return source.get("roomId", "unknown")
    return source.get("userId", "unknown")


def _reply_token(event: dict) -> str:
    """Extract reply token."""
    return event.get("replyToken", "")


def _tenant_id(request: Request) -> str:
    """Resolve tenant id from headers."""
    return request.headers.get("X-Tenant-Id", "default")
