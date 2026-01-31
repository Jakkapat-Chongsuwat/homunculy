"""LINE webhook handler for channel routing."""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from application.use_cases.gateway import RouteInboundInput, RouteInboundUseCase
from infrastructure.container import container

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
    payload = await request.json()
    tenant_id = _tenant_id(request)
    handled = await _handle_events(payload, tenant_id, use_case)
    return LineWebhookResponse(status="ok", handled=handled)


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
