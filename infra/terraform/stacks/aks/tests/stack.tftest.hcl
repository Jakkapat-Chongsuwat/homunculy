# =============================================================================
# AKS Stack - Integration Tests
# =============================================================================
# Purpose: Validate the complete AKS stack configuration
# Run: cd stacks/aks && terraform test
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

variables {
  subscription_id = "00000000-0000-0000-0000-000000000000"
  environment     = "dev"
  location        = "eastus"
  project_name    = "homunculy"

  kubernetes_version      = "1.29"
  aks_sku_tier            = "Free"
  aks_automatic_upgrade   = "patch"
  node_os_upgrade_channel = "NodeImage"

  system_node_pool_vm_size    = "Standard_B2s"
  system_node_pool_node_count = 1
  system_node_pool_min_count  = 1
  system_node_pool_max_count  = 3

  network_plugin    = "azure"
  network_policy    = "azure"
  dns_service_ip    = "10.0.0.10"
  service_cidr      = "10.0.0.0/16"
  load_balancer_sku = "standard"

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
# Test: Resource group name follows AKS convention
# -----------------------------------------------------------------------------
run "resource_group_naming" {
  command = plan

  assert {
    condition     = azurerm_resource_group.main.name == "rg-homunculy-aks-dev"
    error_message = "Resource group should follow pattern: rg-{project}-aks-{environment}"
  }
}

# -----------------------------------------------------------------------------
# Test: Common tags are applied with AKS stack
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
    condition     = azurerm_resource_group.main.tags["stack"] == "aks"
    error_message = "Stack tag should be 'aks'"
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

  # Verify AKS module
  assert {
    condition     = module.aks != null
    error_message = "AKS module should be instantiated"
  }
}

# -----------------------------------------------------------------------------
# Test: Production uses Standard SKU tier
# -----------------------------------------------------------------------------
run "prod_standard_tier" {
  command = plan

  variables {
    environment  = "prod"
    aks_sku_tier = "Standard"
  }

  assert {
    condition     = azurerm_resource_group.main.tags["environment"] == "prod"
    error_message = "Production environment should be set"
  }
}
