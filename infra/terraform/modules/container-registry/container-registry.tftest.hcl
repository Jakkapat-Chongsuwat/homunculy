# =============================================================================
# Container Registry Module - Unit Tests
# =============================================================================
# Purpose: Validate container registry configuration without creating resources
# Run: terraform test -filter=modules/container-registry/container-registry.tftest.hcl
# =============================================================================

# Mock provider to avoid real Azure calls
mock_provider "azurerm" {}

variables {
  resource_group_name = "rg-test"
  location            = "eastus"
  project_name        = "homunculy"
  environment         = "dev"
  sku                 = "Basic"
  admin_enabled       = true
  tags = {
    test = "true"
  }
}

# -----------------------------------------------------------------------------
# Test: Registry name follows naming convention
# -----------------------------------------------------------------------------
run "registry_name_convention" {
  command = plan

  assert {
    condition     = azurerm_container_registry.main.name == "acrhomunculydev"
    error_message = "Container registry name should follow pattern: acr{project}{environment}"
  }
}

# -----------------------------------------------------------------------------
# Test: Registry uses correct SKU for dev environment
# -----------------------------------------------------------------------------
run "registry_sku_dev" {
  command = plan

  assert {
    condition     = azurerm_container_registry.main.sku == "Basic"
    error_message = "Dev environment should use Basic SKU"
  }
}

# -----------------------------------------------------------------------------
# Test: Registry has admin enabled
# -----------------------------------------------------------------------------
run "registry_admin_enabled" {
  command = plan

  assert {
    condition     = azurerm_container_registry.main.admin_enabled == true
    error_message = "Admin should be enabled for development"
  }
}

# -----------------------------------------------------------------------------
# Test: Production uses Standard SKU
# -----------------------------------------------------------------------------
run "registry_sku_prod" {
  command = plan

  variables {
    environment = "prod"
    sku         = "Standard"
  }

  assert {
    condition     = azurerm_container_registry.main.sku == "Standard"
    error_message = "Prod environment should use Standard SKU"
  }
}

# -----------------------------------------------------------------------------
# Test: Registry has correct tags
# -----------------------------------------------------------------------------
run "registry_tags" {
  command = plan

  assert {
    condition     = azurerm_container_registry.main.tags["component"] == "container-registry"
    error_message = "Registry should have component=container-registry tag"
  }
}

# -----------------------------------------------------------------------------
# Test: Registry location is correct
# -----------------------------------------------------------------------------
run "registry_location" {
  command = plan

  assert {
    condition     = azurerm_container_registry.main.location == "eastus"
    error_message = "Registry location should match specified location"
  }
}
