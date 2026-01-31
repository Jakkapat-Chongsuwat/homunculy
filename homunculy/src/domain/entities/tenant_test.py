"""Unit tests for Tenant entity."""

from domain.entities.tenant import Tenant


def test_create_tenant() -> None:
    tenant = Tenant(id="t1", name="Tenant One")
    assert tenant.id == "t1"
    assert tenant.name == "Tenant One"
    assert tenant.is_active is True


def test_tenant_metadata_default() -> None:
    tenant = Tenant(id="t1", name="Tenant One")
    assert tenant.metadata == {}
