# =============================================================================
# AKS Module - Unit Tests
# =============================================================================
# Purpose: Validate AKS cluster configuration and settings
# Run: terraform test (from modules/aks directory)
# =============================================================================

# Mock providers to avoid real Azure calls
mock_provider "azurerm" {}

variables {
  resource_group_name = "rg-test"
  resource_group_id   = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg-test"
  location            = "eastus"
  project_name        = "homunculy"
  environment         = "dev"

  kubernetes_version      = "1.29"
  sku_tier                = "Free"
  automatic_upgrade       = "patch"
  node_os_upgrade_channel = "NodeImage"

  system_node_pool_vm_size    = "Standard_B2s"
  system_node_pool_node_count = 1
  system_node_pool_min_count  = 1
  system_node_pool_max_count  = 3

  create_user_node_pool     = false
  user_node_pool_vm_size    = "Standard_B2s"
  user_node_pool_node_count = 1
  user_node_pool_min_count  = 0
  user_node_pool_max_count  = 5

  network_plugin    = "azure"
  network_policy    = "azure"
  dns_service_ip    = "10.0.0.10"
  service_cidr      = "10.0.0.0/16"
  load_balancer_sku = "standard"

  log_analytics_workspace_id = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg-test/providers/Microsoft.OperationalInsights/workspaces/log-test"

  # Empty to skip role assignments (mock provider can't provide kubelet_identity)
  container_registry_id = ""
  keyvault_id           = ""

  # Production security features (disabled by default for tests)
  private_cluster_enabled    = false
  azure_policy_enabled       = false
  microsoft_defender_enabled = false
  aks_subnet_id              = null

  tags = {
    test = "true"
  }
}

# -----------------------------------------------------------------------------
# Test: AKS cluster name convention
# -----------------------------------------------------------------------------
run "cluster_name_convention" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_kubernetes_cluster.main.name == "aks-homunculy-dev"
    error_message = "AKS cluster name should follow pattern: aks-{project}-{environment}"
  }
}

# -----------------------------------------------------------------------------
# Test: AKS cluster DNS prefix
# -----------------------------------------------------------------------------
run "cluster_dns_prefix" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_kubernetes_cluster.main.dns_prefix == "homunculy-dev"
    error_message = "AKS DNS prefix should follow pattern: {project}-{environment}"
  }
}

# -----------------------------------------------------------------------------
# Test: AKS uses correct Kubernetes version
# -----------------------------------------------------------------------------
run "kubernetes_version" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_kubernetes_cluster.main.kubernetes_version == "1.29"
    error_message = "AKS should use specified Kubernetes version"
  }
}

# -----------------------------------------------------------------------------
# Test: Dev environment uses Free tier
# -----------------------------------------------------------------------------
run "dev_sku_tier" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_kubernetes_cluster.main.sku_tier == "Free"
    error_message = "Dev environment should use Free SKU tier"
  }
}

# -----------------------------------------------------------------------------
# Test: Prod environment uses Standard tier
# -----------------------------------------------------------------------------
run "prod_sku_tier" {
  command = plan

  variables {
    environment = "prod"
    sku_tier    = "Standard"
  }

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_kubernetes_cluster.main.sku_tier == "Standard"
    error_message = "Prod environment should use Standard SKU tier"
  }
}

# -----------------------------------------------------------------------------
# Test: OIDC issuer is enabled for workload identity
# -----------------------------------------------------------------------------
run "oidc_issuer_enabled" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_kubernetes_cluster.main.oidc_issuer_enabled == true
    error_message = "OIDC issuer should be enabled for workload identity"
  }
}

# -----------------------------------------------------------------------------
# Test: Workload identity is enabled
# -----------------------------------------------------------------------------
run "workload_identity_enabled" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_kubernetes_cluster.main.workload_identity_enabled == true
    error_message = "Workload identity should be enabled"
  }
}

# -----------------------------------------------------------------------------
# Test: System node pool name
# -----------------------------------------------------------------------------
run "system_node_pool_name" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_kubernetes_cluster.main.default_node_pool[0].name == "system"
    error_message = "System node pool should be named 'system'"
  }
}

# -----------------------------------------------------------------------------
# Test: System node pool autoscaling enabled
# -----------------------------------------------------------------------------
run "system_node_pool_autoscaling" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_kubernetes_cluster.main.default_node_pool[0].auto_scaling_enabled == true
    error_message = "System node pool should have autoscaling enabled"
  }
}

# -----------------------------------------------------------------------------
# Test: System node pool min/max counts
# -----------------------------------------------------------------------------
run "system_node_pool_scaling_limits" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_kubernetes_cluster.main.default_node_pool[0].min_count == 1
    error_message = "System node pool min_count should be 1"
  }

  assert {
    condition     = azurerm_kubernetes_cluster.main.default_node_pool[0].max_count == 3
    error_message = "System node pool max_count should be 3"
  }
}

# -----------------------------------------------------------------------------
# Test: Network plugin is Azure CNI
# -----------------------------------------------------------------------------
run "network_plugin_azure" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_kubernetes_cluster.main.network_profile[0].network_plugin == "azure"
    error_message = "Network plugin should be Azure CNI"
  }
}

# -----------------------------------------------------------------------------
# Test: Network policy is Azure
# -----------------------------------------------------------------------------
run "network_policy_azure" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_kubernetes_cluster.main.network_profile[0].network_policy == "azure"
    error_message = "Network policy should be Azure"
  }
}

# -----------------------------------------------------------------------------
# Test: Load balancer SKU is standard
# -----------------------------------------------------------------------------
run "load_balancer_sku_standard" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_kubernetes_cluster.main.network_profile[0].load_balancer_sku == "standard"
    error_message = "Load balancer SKU should be standard"
  }
}

# -----------------------------------------------------------------------------
# Test: Key Vault secrets provider enabled
# -----------------------------------------------------------------------------
run "keyvault_secrets_provider" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_kubernetes_cluster.main.key_vault_secrets_provider[0].secret_rotation_enabled == true
    error_message = "Key Vault secrets provider should have secret rotation enabled"
  }
}

# -----------------------------------------------------------------------------
# Test: User assigned identity name convention
# -----------------------------------------------------------------------------
run "identity_name_convention" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_user_assigned_identity.aks.name == "id-homunculy-aks-dev"
    error_message = "AKS identity name should follow pattern: id-{project}-aks-{environment}"
  }
}

# -----------------------------------------------------------------------------
# Test: Automatic upgrade channel is patch
# -----------------------------------------------------------------------------
run "automatic_upgrade_channel" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_kubernetes_cluster.main.automatic_upgrade_channel == "patch"
    error_message = "Automatic upgrade channel should be 'patch'"
  }
}

# -----------------------------------------------------------------------------
# Test: User node pool is not created by default
# -----------------------------------------------------------------------------
run "no_user_node_pool_by_default" {
  command = plan

  module {
    source = "./."
  }

  # When create_user_node_pool is false, the count should be 0
  # We check this by verifying the resource doesn't exist in the plan
  assert {
    condition     = length([for np in azurerm_kubernetes_cluster_node_pool.user : np]) == 0
    error_message = "User node pool should not be created when create_user_node_pool is false"
  }
}

# -----------------------------------------------------------------------------
# Test: User node pool is created when enabled
# -----------------------------------------------------------------------------
run "user_node_pool_created_when_enabled" {
  command = plan

  variables {
    create_user_node_pool = true
  }

  module {
    source = "./."
  }

  assert {
    condition     = length([for np in azurerm_kubernetes_cluster_node_pool.user : np]) == 1
    error_message = "User node pool should be created when create_user_node_pool is true"
  }
}

# =============================================================================
# Production Security Feature Tests
# =============================================================================

# -----------------------------------------------------------------------------
# Test: Azure Policy disabled by default
# -----------------------------------------------------------------------------
run "azure_policy_disabled_by_default" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_kubernetes_cluster.main.azure_policy_enabled == false
    error_message = "Azure Policy should be disabled by default"
  }
}

# -----------------------------------------------------------------------------
# Test: Azure Policy enabled when set
# -----------------------------------------------------------------------------
run "azure_policy_enabled_when_set" {
  command = plan

  variables {
    azure_policy_enabled = true
  }

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_kubernetes_cluster.main.azure_policy_enabled == true
    error_message = "Azure Policy should be enabled when azure_policy_enabled is true"
  }
}

# -----------------------------------------------------------------------------
# Test: Private cluster disabled by default
# -----------------------------------------------------------------------------
run "private_cluster_disabled_by_default" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_kubernetes_cluster.main.private_cluster_enabled == false
    error_message = "Private cluster should be disabled by default"
  }
}

# -----------------------------------------------------------------------------
# Test: Private cluster enabled when set
# -----------------------------------------------------------------------------
run "private_cluster_enabled_when_set" {
  command = plan

  variables {
    private_cluster_enabled = true
  }

  module {
    source = "./."
  }

  assert {
    condition     = azurerm_kubernetes_cluster.main.private_cluster_enabled == true
    error_message = "Private cluster should be enabled when private_cluster_enabled is true"
  }
}

# -----------------------------------------------------------------------------
# Test: Microsoft Defender disabled by default
# -----------------------------------------------------------------------------
run "microsoft_defender_disabled_by_default" {
  command = plan

  module {
    source = "./."
  }

  assert {
    condition     = length(azurerm_kubernetes_cluster.main.microsoft_defender) == 0
    error_message = "Microsoft Defender should be disabled by default"
  }
}

# -----------------------------------------------------------------------------
# Test: Microsoft Defender enabled when set
# -----------------------------------------------------------------------------
run "microsoft_defender_enabled_when_set" {
  command = plan

  variables {
    microsoft_defender_enabled = true
  }

  module {
    source = "./."
  }

  assert {
    condition     = length(azurerm_kubernetes_cluster.main.microsoft_defender) == 1
    error_message = "Microsoft Defender should be enabled when microsoft_defender_enabled is true"
  }
}
