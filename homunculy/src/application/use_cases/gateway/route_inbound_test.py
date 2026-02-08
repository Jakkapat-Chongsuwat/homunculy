"""Unit tests for RouteInboundUseCase."""

import pytest

from application.use_cases.gateway import RouteInboundInput, RouteInboundUseCase
from domain.interfaces import (
    ChannelClientPort,
    ChannelOutbound,
    OrchestrationInput,
    OrchestrationOutput,
    OrchestratorPort,
    SessionStorePort,
    TenantPolicyPort,
)
from infrastructure.persistence.session import InMemorySessionStore


class _AllowAll(TenantPolicyPort):
    def allow(self, inbound) -> bool:
        return True


class _DenyAll(TenantPolicyPort):
    def allow(self, inbound) -> bool:
        return False


class _StubOrchestrator(OrchestratorPort):
    async def invoke(self, input_: OrchestrationInput) -> OrchestrationOutput:
        return OrchestrationOutput(message=f"ok:{input_.message}")

    async def stream(self, input_: OrchestrationInput):
        yield f"ok:{input_.message}"


class _SpyChannel(ChannelClientPort):
    def __init__(self) -> None:
        self.sent: list[ChannelOutbound] = []

    async def send(self, message: ChannelOutbound) -> None:
        self.sent.append(message)


def _use_case(policy: TenantPolicyPort, store: SessionStorePort, channel: ChannelClientPort):
    orchestrator = _StubOrchestrator()
    return RouteInboundUseCase(orchestrator, store, policy, channel)


@pytest.mark.asyncio
async def test_routes_allowed_message() -> None:
    store = InMemorySessionStore()
    channel = _SpyChannel()
    use_case = _use_case(_AllowAll(), store, channel)

    input_ = RouteInboundInput("t1", "line", "u1", "hello", {})
    output = await use_case.execute(input_)

    assert output.allowed is True
    assert output.response_text.startswith("ok:")
    assert channel.sent[0].text.startswith("ok:")


@pytest.mark.asyncio
async def test_blocks_denied_message() -> None:
    store = InMemorySessionStore()
    channel = _SpyChannel()
    use_case = _use_case(_DenyAll(), store, channel)

    input_ = RouteInboundInput("t1", "line", "u1", "hello", {})
    output = await use_case.execute(input_)

    assert output.allowed is False
    assert channel.sent == []
