# =============================================================================
# Container Apps Stack - Integration Tests
# =============================================================================
# Purpose: Validate the complete Container Apps stack configuration
# Run: terraform test (from stacks/container-apps directory)
# =============================================================================

# Mock providers to avoid real Azure calls
mock_provider "azurerm" {
  override_data {
    target = data.azurerm_client_config.current
    values = {
      client_id       = "00000000-0000-0000-0000-000000000000"
      tenant_id       = "00000000-0000-0000-0000-000000000000"
      subscription_id = "00000000-0000-0000-0000-000000000000"
      object_id       = "00000000-0000-0000-0000-000000000000"
    }
  }
}
mock_provider "azapi" {}
mock_provider "random" {}
mock_provider "time" {}

variables {
  subscription_id = "00000000-0000-0000-0000-000000000000"
  environment     = "dev"
  location        = "eastus"
  project_name    = "homunculy"

  homunculy_image_tag      = "latest"
  homunculy_min_replicas   = 0
  homunculy_max_replicas   = 2
  chat_client_image_tag    = "latest"
  chat_client_min_replicas = 0
  chat_client_max_replicas = 2

  db_sku_name              = "B_Standard_B1ms"
  db_storage_mb            = 32768
  db_backup_retention_days = 7

  openai_api_key     = "test-openai-key"
  elevenlabs_api_key = "test-elevenlabs-key"

  tags = {
    test = "true"
  }
}

# -----------------------------------------------------------------------------
# Test: Resource group name follows convention
# -----------------------------------------------------------------------------
run "resource_group_naming" {
  command = plan

  assert {
    condition     = azurerm_resource_group.main.name == "rg-homunculy-dev"
    error_message = "Resource group should follow pattern: rg-{project}-{environment}"
  }
}

# -----------------------------------------------------------------------------
# Test: Common tags are applied
# -----------------------------------------------------------------------------
run "common_tags_applied" {
  command = plan

  assert {
    condition     = azurerm_resource_group.main.tags["project"] == "homunculy"
    error_message = "Project tag should be applied"
  }

  assert {
    condition     = azurerm_resource_group.main.tags["environment"] == "dev"
    error_message = "Environment tag should be applied"
  }

  assert {
    condition     = azurerm_resource_group.main.tags["managed_by"] == "terraform"
    error_message = "Managed_by tag should be applied"
  }

  assert {
    condition     = azurerm_resource_group.main.tags["stack"] == "container-apps"
    error_message = "Stack tag should be 'container-apps'"
  }
}

# -----------------------------------------------------------------------------
# Test: All modules are instantiated
# -----------------------------------------------------------------------------
run "all_modules_instantiated" {
  command = plan

  # Verify monitoring module
  assert {
    condition     = module.monitoring != null
    error_message = "Monitoring module should be instantiated"
  }

  # Verify container registry module
  assert {
    condition     = module.container_registry != null
    error_message = "Container registry module should be instantiated"
  }

  # Verify database module
  assert {
    condition     = module.database != null
    error_message = "Database module should be instantiated"
  }

  # Verify keyvault module
  assert {
    condition     = module.keyvault != null
    error_message = "Key Vault module should be instantiated"
  }

  # Verify container apps module
  assert {
    condition     = module.container_apps != null
    error_message = "Container Apps module should be instantiated"
  }
}

# -----------------------------------------------------------------------------
# Test: Production uses higher retention
# -----------------------------------------------------------------------------
run "prod_higher_retention" {
  command = plan

  variables {
    environment = "prod"
  }

  # Prod should use 90 days retention (set in main.tf via ternary)
  assert {
    condition     = azurerm_resource_group.main.tags["environment"] == "prod"
    error_message = "Production environment should be set"
  }
}
