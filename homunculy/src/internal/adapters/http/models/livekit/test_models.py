import pytest
from pydantic import ValidationError

from internal.adapters.http.models.livekit import CreateJoinTokenRequest


def test_create_join_token_defaults():
    req = CreateJoinTokenRequest(tenant_id="t1", session_id="s1")
    assert req.ttl_seconds == 3600
    assert req.identity == ""


def test_create_join_token_ttl_validation():
    with pytest.raises(ValidationError):
        CreateJoinTokenRequest(tenant_id="t1", session_id="s1", ttl_seconds=0)
