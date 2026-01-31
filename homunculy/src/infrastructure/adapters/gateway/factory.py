"""Gateway adapter factory helpers."""

from domain.interfaces import (
    ChannelClientPort,
    OrchestratorPort,
    SessionStorePort,
    TenantPolicyPort,
)
from infrastructure.adapters.channels import LineChannelClient
from infrastructure.adapters.gateway.orchestrator import GatewayOrchestrator
from infrastructure.adapters.gateway.policy import AllowAllTenantPolicy
from infrastructure.persistence.redislite_session_store import RedisliteSessionStore
from infrastructure.persistence.session_store import InMemorySessionStore
from infrastructure.persistence.sqlite_session_store import SQLiteSessionStore
from settings.config import settings


def create_channel_client() -> ChannelClientPort:
    """Create channel client (LINE stub by default)."""
    return LineChannelClient()


def create_session_store() -> SessionStorePort:
    """Create session store implementation."""
    return _sqlite_store() or _embedded_store() or InMemorySessionStore()


def _sqlite_store() -> SessionStorePort | None:
    """Create SQLite store if enabled."""
    cfg = settings.gateway
    return SQLiteSessionStore(cfg.sqlite_file) if cfg.use_sqlite else None


def _embedded_store() -> SessionStorePort | None:
    """Create embedded Redis store if enabled."""
    cfg = settings.gateway
    if not cfg.redis_embedded:
        return None
    try:
        return RedisliteSessionStore(cfg.redis_file)
    except RuntimeError:
        return None


def create_tenant_policy() -> TenantPolicyPort:
    """Create tenant policy implementation."""
    return AllowAllTenantPolicy()


def create_gateway_orchestrator(dual_system) -> OrchestratorPort:
    """Create gateway orchestrator wrapper."""
    return GatewayOrchestrator(dual_system)
