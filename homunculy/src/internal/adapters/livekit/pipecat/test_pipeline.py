from types import SimpleNamespace

from internal.adapters.livekit.pipecat.pipeline import (
    default_configuration,
    default_model,
    default_system_prompt,
    livekit_parts,
)
from internal.domain.entities import AgentProvider


def test_default_model_fallback():
    assert default_model() == "gpt-4o-mini"


def test_default_system_prompt_fallback():
    assert default_system_prompt() == "You are a helpful assistant."


def test_default_configuration_provider():
    config = default_configuration()
    assert config.provider == AgentProvider.LANGRAPH


def test_livekit_parts_extracts_values():
    ctx = SimpleNamespace(
        _info=SimpleNamespace(url="wss://lk", token="tok"), room=SimpleNamespace(name="room")
    )
    assert livekit_parts(ctx) == ("wss://lk", "tok", "room")
