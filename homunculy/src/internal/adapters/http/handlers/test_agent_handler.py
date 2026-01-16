from internal.adapters.http.handlers.agent_handler import (
    _audio_payload,
    _metadata_payload,
)


def test_metadata_payload_defaults_tools_called():
    payload = _metadata_payload({"model_used": "gpt-4o-mini"})
    assert payload["tools_called"] == []


def test_audio_payload_generated_flag():
    payload = _audio_payload({"data": "abc"})
    assert payload["generated"] is True
