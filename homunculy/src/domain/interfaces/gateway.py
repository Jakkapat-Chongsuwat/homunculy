"""Gateway ports for channel routing."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from domain.entities import Session


@dataclass(frozen=True)
class ChannelInbound:
    """Inbound channel message data."""

    tenant_id: str
    channel: str
    user_id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ChannelOutbound:
    """Outbound channel message data."""

    tenant_id: str
    channel: str
    user_id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


class ChannelClientPort(ABC):
    """Outbound channel client."""

    @abstractmethod
    async def send(self, message: ChannelOutbound) -> None:
        """Send outbound message."""
        ...


class SessionStorePort(ABC):
    """Session store for channel routing."""

    @abstractmethod
    def get_or_create(self, inbound: ChannelInbound) -> Session:
        """Get or create session for inbound message."""
        ...

    @abstractmethod
    def save(self, session: Session) -> None:
        """Persist updated session."""
        ...


class TenantPolicyPort(ABC):
    """Tenant policy enforcement."""

    @abstractmethod
    def allow(self, inbound: ChannelInbound) -> bool:
        """Check if inbound message is allowed."""
        ...


class ChannelTokenProviderPort(ABC):
    """Provide channel tokens per tenant/target."""

    @abstractmethod
    def get_token(self, tenant_id: str, channel: str, target_id: str) -> str | None:
        """Get token for outbound channel call."""
        ...

    @abstractmethod
    def get_secret(self, tenant_id: str, channel: str, target_id: str) -> str | None:
        """Get secret for inbound channel verification."""
        ...
