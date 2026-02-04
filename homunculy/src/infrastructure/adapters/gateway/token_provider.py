"""Channel token provider backed by config file and env vars."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

from common.logger import get_logger
from domain.interfaces import ChannelTokenProviderPort
from settings.config import settings

logger = get_logger(__name__)


@dataclass(frozen=True)
class _TokenRule:
    token_env: str | None
    secret_env: str | None


class ConfigTokenProvider(ChannelTokenProviderPort):
    """Token provider using channels config file."""

    def __init__(self, config_path: str | None = None) -> None:
        self._path = config_path or settings.gateway.channels_config_file
        self._config = _load_config(self._path)

    def get_token(self, tenant_id: str, channel: str, target_id: str) -> str | None:
        """Get token for outbound channel call."""
        rule = _rule_for(self._config, tenant_id, channel, target_id)
        return os.getenv(rule.token_env) if rule and rule.token_env else None

    def get_secret(self, tenant_id: str, channel: str, target_id: str) -> str | None:
        """Get secret for inbound channel verification."""
        rule = _rule_for(self._config, tenant_id, channel, target_id)
        return os.getenv(rule.secret_env) if rule and rule.secret_env else None


def _load_config(path: str) -> dict:
    """Load channels config file."""
    if not os.path.exists(path):
        logger.warning("Channel config not found", path=path)
        return {"tenants": {}}
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _rule_for(config: dict, tenant_id: str, channel: str, target_id: str) -> _TokenRule | None:
    """Resolve token rule from config."""
    tenant = _tenant(config, tenant_id)
    if not tenant:
        return None
    channel_cfg = _channel(tenant, channel)
    if not channel_cfg:
        return None
    target_rule = _target_rule(channel_cfg, target_id)
    return target_rule or _default_rule(channel_cfg)


def _tenant(config: dict, tenant_id: str) -> dict | None:
    """Get tenant config."""
    return config.get("tenants", {}).get(tenant_id)


def _channel(tenant: dict, channel: str) -> dict | None:
    """Get channel config."""
    return tenant.get("channels", {}).get(channel)


def _target_rule(channel_cfg: dict, target_id: str) -> _TokenRule | None:
    """Get target-specific rule if present."""
    target = channel_cfg.get("targets", {}).get(target_id)
    return _token_rule(target) if target else None


def _default_rule(channel_cfg: dict) -> _TokenRule | None:
    """Get default token rule."""
    return _token_rule(channel_cfg)


def _token_rule(cfg: dict | None) -> _TokenRule | None:
    """Build token rule from config."""
    if not cfg:
        return None
    return _TokenRule(cfg.get("token_env"), cfg.get("secret_env"))
