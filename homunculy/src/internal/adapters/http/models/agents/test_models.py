from internal.adapters.http.models.agents import (
    AgentConfigurationRequest,
    AgentPersonalityRequest,
    AudioResponse,
)


def test_agent_configuration_defaults():
    personality = AgentPersonalityRequest(name="A", description="D")
    req = AgentConfigurationRequest(personality=personality)
    assert req.provider == "langraph"
    assert req.model_name == "gpt-4"


def test_audio_response_defaults():
    audio = AudioResponse()
    assert audio.data == ""
    assert audio.generated is False
