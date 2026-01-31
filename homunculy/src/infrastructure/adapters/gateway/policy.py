"""Tenant policy adapters."""

from domain.interfaces import ChannelInbound, TenantPolicyPort


class AllowAllTenantPolicy(TenantPolicyPort):
    """Allow all inbound messages."""

    def allow(self, inbound: ChannelInbound) -> bool:
        """Always allow inbound messages."""
        return True
