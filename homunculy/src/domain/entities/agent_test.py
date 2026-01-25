"""Unit tests for Agent domain entity."""

from datetime import datetime, timezone

import pytest

from domain.entities.agent import (
    Agent,
    AgentConfiguration,
    AgentMessage,
    AgentPersonality,
    AgentProvider,
    AgentResponse,
    AgentStatus,
    AgentThread,
)


class TestAgentProvider:
    """Tests for AgentProvider enum."""

    def test_openai_value(self) -> None:
        assert AgentProvider.OPENAI.value == "openai"

    def test_langraph_value(self) -> None:
        assert AgentProvider.LANGRAPH.value == "langraph"


class TestAgentStatus:
    """Tests for AgentStatus enum."""

    def test_all_statuses_exist(self) -> None:
        statuses = ["idle", "thinking", "responding", "error", "completed"]
        for status in statuses:
            assert status in [s.value for s in AgentStatus]


class TestAgentMessage:
    """Tests for AgentMessage dataclass."""

    def test_create_message(self) -> None:
        now = datetime.now(timezone.utc)
        msg = AgentMessage(role="user", content="Hello", timestamp=now)
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_message_with_metadata(self) -> None:
        now = datetime.now(timezone.utc)
        msg = AgentMessage(
            role="assistant",
            content="Hi!",
            timestamp=now,
            metadata={"tokens": 10},
        )
        assert msg.metadata == {"tokens": 10}


class TestAgentResponse:
    """Tests for AgentResponse model."""

    def test_create_response(self) -> None:
        resp = AgentResponse(message="Hello!", confidence=0.95)
        assert resp.message == "Hello!"
        assert resp.confidence == 0.95
        assert resp.status == AgentStatus.COMPLETED

    def test_response_with_reasoning(self) -> None:
        resp = AgentResponse(
            message="Result",
            confidence=0.8,
            reasoning="Based on context",
        )
        assert resp.reasoning == "Based on context"


class TestAgentPersonality:
    """Tests for AgentPersonality model."""

    def test_create_personality(self) -> None:
        p = AgentPersonality(name="Aria", description="Helpful assistant")
        assert p.name == "Aria"
        assert p.description == "Helpful assistant"
        assert p.mood == "neutral"

    def test_personality_with_traits(self) -> None:
        p = AgentPersonality(
            name="Test",
            description="Test agent",
            traits={"friendly": 0.9},
        )
        assert p.traits["friendly"] == 0.9


class TestAgentConfiguration:
    """Tests for AgentConfiguration model."""

    @pytest.fixture
    def personality(self) -> AgentPersonality:
        return AgentPersonality(name="Test", description="Test")

    def test_create_config(self, personality: AgentPersonality) -> None:
        cfg = AgentConfiguration(
            provider=AgentProvider.LANGRAPH,
            model_name="gpt-4o",
            personality=personality,
        )
        assert cfg.provider == AgentProvider.LANGRAPH
        assert cfg.model_name == "gpt-4o"

    def test_config_defaults(self, personality: AgentPersonality) -> None:
        cfg = AgentConfiguration(
            provider=AgentProvider.OPENAI,
            model_name="gpt-4",
            personality=personality,
        )
        assert cfg.temperature == 0.7
        assert cfg.max_tokens == 2000
        assert cfg.tools == []


class TestAgent:
    """Tests for Agent entity."""

    @pytest.fixture
    def config(self) -> AgentConfiguration:
        p = AgentPersonality(name="Test", description="Test")
        return AgentConfiguration(
            provider=AgentProvider.LANGRAPH,
            model_name="gpt-4o",
            personality=p,
        )

    def test_create_agent(self, config: AgentConfiguration) -> None:
        agent = Agent(id="agent-1", name="TestAgent", configuration=config)
        assert agent.id == "agent-1"
        assert agent.name == "TestAgent"
        assert agent.is_active is True

    def test_agent_activate(self, config: AgentConfiguration) -> None:
        agent = Agent(id="a1", name="Test", configuration=config, is_active=False)
        agent.activate()
        assert agent.is_active is True

    def test_agent_deactivate(self, config: AgentConfiguration) -> None:
        agent = Agent(id="a1", name="Test", configuration=config, is_active=True)
        agent.deactivate()
        assert agent.is_active is False


class TestAgentThread:
    """Tests for AgentThread model."""

    def test_create_thread(self) -> None:
        thread = AgentThread(id="t1", agent_id="a1")
        assert thread.id == "t1"
        assert thread.agent_id == "a1"
        assert thread.messages == []
