"""LiveKit HTTP handler.

Issues room join tokens for WebRTC clients.
"""

from fastapi import APIRouter

from internal.adapters.http.models.livekit import CreateJoinTokenRequest, CreateJoinTokenResponse
from internal.infrastructure.services.livekit import create_join_token

router = APIRouter(prefix="/api/v1/livekit", tags=["LiveKit"])


@router.post("/token", response_model=CreateJoinTokenResponse)
async def create_token(req: CreateJoinTokenRequest) -> CreateJoinTokenResponse:
    return _build_join_token_response(req)


def _build_join_token_response(req: CreateJoinTokenRequest) -> CreateJoinTokenResponse:
    url, room, token = create_join_token(**_join_token_args(req))
    return CreateJoinTokenResponse(url=url, room=room, token=token)


def _join_token_args(req: CreateJoinTokenRequest) -> dict:
    return dict(
        tenant_id=req.tenant_id,
        session_id=req.session_id,
        identity=req.identity,
        name=req.name,
        metadata=req.metadata,
        ttl=req.ttl_seconds,
    )
