from unittest.mock import patch

import pytest

from internal.adapters.http.handlers import livekit_handler
from internal.adapters.http.models.livekit import CreateJoinTokenRequest


@pytest.mark.asyncio
async def test_create_token_returns_join_token_response():
    req = CreateJoinTokenRequest(tenant_id="t1", session_id="s1")
    with patch("internal.adapters.http.handlers.livekit_handler.create_join_token") as creator:
        creator.return_value = ("wss://lk", "room", "token")
        response = await livekit_handler.create_token(req)
    assert response.url == "wss://lk"
    assert response.room == "room"
    assert response.token == "token"
